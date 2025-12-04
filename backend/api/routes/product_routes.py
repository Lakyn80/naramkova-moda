import os
import uuid
from flask import Blueprint, jsonify, request, url_for, current_app
from werkzeug.utils import secure_filename

from backend.extensions import db
from backend.models import Product, ProductMedia, Category

api_products = Blueprint("api_products", __name__, url_prefix="/api/products")

# --- Volitelné závislosti pro robustní práci s obrázky ---
try:
    from PIL import Image, ImageOps
    PIL_OK = True
except Exception:
    PIL_OK = False

# HEIC (iPhone) podpora je volitelná – pokud je nainstalováno pillow-heif, zaregistrujeme dekodér
if PIL_OK:
    try:
        import pillow_heif  # type: ignore
        pillow_heif.register_heif_opener()
    except Exception:
        pass


# ========================= Pomocné funkce =========================

def _detect_media_type(filename: str, mimetype: str | None) -> str:
    """Určí typ média – 'video' nebo 'image'."""
    mt = (mimetype or "").lower()
    if mt.startswith("video/"):
        return "video"
    if mt.startswith("image/"):
        return "image"
    ext = os.path.splitext(filename)[1].lower()
    if ext in {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}:
        return "video"
    return "image"


def _uploads_dir() -> str:
    d = os.path.join(current_app.root_path, "static", "uploads")
    os.makedirs(d, exist_ok=True)
    return d


def _safe_uuid_name(ext: str = ".webp") -> str:
    """Vytvoří bezpečný název souboru `uuid.ext`."""
    return f"{uuid.uuid4().hex}{ext.lower()}"


def _save_raw(fs) -> str:
    """
    Fallback, pokud není PIL: uloží originál beze změny (jen secure_filename).
    Vrací relativní název souboru (bez 'uploads/').
    """
    upload_dir = _uploads_dir()
    fn = secure_filename(fs.filename or _safe_uuid_name(os.path.splitext(fs.filename or "")[1] or ".bin"))
    path = os.path.join(upload_dir, fn)
    fs.save(path)
    return fn


def _process_and_save_image(fs) -> str:
    """
    Normalizace obrázku:
    - EXIF orientace
    - RGB
    - max 1600x1600
    - WebP (quality 85)
    Vrací relativní název .webp (bez 'uploads/').
    Pokud PIL není dostupné → uloží se surový soubor (_save_raw).
    """
    if not PIL_OK:
        return _save_raw(fs)

    try:
        # Načtení přes PIL (pillow-heif umožní HEIC/HEIF)
        img = Image.open(fs.stream if hasattr(fs, "stream") else fs)
        # EXIF auto-rotate
        img = ImageOps.exif_transpose(img)
        # Konverze do RGB (odstranění profilů/CMYK apod.)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        # Zmenšit dlouhou stranu na max 1600
        img.thumbnail((1600, 1600), Image.Resampling.LANCZOS)

        # Pokud je RGBA, převedeme na RGB s bílým pozadím (aby WebP nemělo nečekanou průhlednost)
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg

        out_name = _safe_uuid_name(".webp")
        out_path = os.path.join(_uploads_dir(), out_name)
        img.save(out_path, format="WEBP", quality=85, method=6)
        return out_name
    except Exception:
        # Když se cokoliv pokazí, alespoň uložíme originál
        return _save_raw(fs)


def _product_dict(product: Product):
    category_name = product.category.name if product.category else None
    category_group = product.category.group if product.category else None

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price_czk,
        "stock": product.stock,  # ✅ zachováno
        "category_id": product.category_id,
        "category_name": category_name,
        # Use relative URLs so frontend can prefix with its own origin/port
        "image_url": f"/static/uploads/{product.image}" if product.image else None,
        "media": [f"/static/uploads/{m.filename}" for m in (product.media or [])],
        "categories": ([category_name] if category_name else []),
        "category_group": category_group,
    }


# ========================= Endpoints =========================

@api_products.get("/")
def get_products():
    # ✅ filtrujeme jen produkty se stock > 0
    items = Product.query.filter(Product.stock > 0).order_by(Product.id.desc()).all()
    return jsonify([_product_dict(p) for p in items]), 200


@api_products.get("/<int:product_id>")
def get_product(product_id: int):
    p = Product.query.get_or_404(product_id)
    return jsonify(_product_dict(p)), 200


@api_products.post("/")
def add_product():
    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    price_raw = (request.form.get("price") or "").strip()
    stock_raw = (request.form.get("stock") or "").strip()
    category_id = request.form.get("category_id")

    if not name or not price_raw or not category_id:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        price = float(price_raw)
    except ValueError:
        return jsonify({"error": "Invalid price"}), 400

    try:
        stock = int(stock_raw) if stock_raw else 1
        if stock < 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Invalid stock"}), 400

    p = Product(
        name=name,
        description=(description or None),
        price_czk=price,
        stock=stock,  # ✅ uložíme počet kusů
        category_id=int(category_id),
    )

    # --- Hlavní obrázek: vždy normalizujeme do WebP ---
    image_file = request.files.get("image")
    if image_file and image_file.filename:
        # Uloží se jako <uuid>.webp (nebo originál, když PIL není)
        normalized = _process_and_save_image(image_file)
        p.image = normalized

    db.session.add(p)
    db.session.flush()

    # --- Další média: obrázky převést do WebP; videa ponechat ---
    for mf in request.files.getlist("media"):
        if not mf or not mf.filename:
            continue
        media_type = _detect_media_type(mf.filename, mf.mimetype)
        if media_type == "image":
            saved_name = _process_and_save_image(mf)
        else:
            # video → ulož surově (bez změny)
            saved_name = _save_raw(mf)
        db.session.add(ProductMedia(product_id=p.id, filename=saved_name, media_type=media_type))

    db.session.commit()
    return jsonify(_product_dict(p)), 201


@api_products.put("/<int:product_id>")
def update_product(product_id: int):
    p = Product.query.get_or_404(product_id)

    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    price_raw = (request.form.get("price") or "").strip()
    stock_raw = (request.form.get("stock") or "").strip()
    category_id = request.form.get("category_id")

    if name:
        p.name = name
    p.description = (description or None)
    if price_raw:
        try:
            p.price_czk = float(price_raw)
        except ValueError:
            return jsonify({"error": "Invalid price"}), 400
    if stock_raw:
        try:
            stock = int(stock_raw)
            if stock < 0:
                raise ValueError
            p.stock = stock
        except ValueError:
            return jsonify({"error": "Invalid stock"}), 400
    if category_id:
        p.category_id = int(category_id)

    # --- Hlavní obrázek: při změně normalizovat do WebP ---
    image_file = request.files.get("image")
    if image_file and image_file.filename:
        normalized = _process_and_save_image(image_file)
        p.image = normalized

    # --- Další média ---
    for mf in request.files.getlist("media"):
        if not mf or not mf.filename:
            continue
        media_type = _detect_media_type(mf.filename, mf.mimetype)
        if media_type == "image":
            saved_name = _process_and_save_image(mf)
        else:
            saved_name = _save_raw(mf)
        db.session.add(ProductMedia(product_id=p.id, filename=saved_name, media_type=media_type))

    db.session.commit()
    return jsonify(_product_dict(p)), 200


@api_products.delete("/<int:product_id>")
def delete_product(product_id: int):
    p = Product.query.get_or_404(product_id)

    if p.image:
        try:
            os.remove(os.path.join(current_app.root_path, "static", "uploads", p.image))
        except Exception:
            pass

    for m in list(p.media or []):
        try:
            os.remove(os.path.join(current_app.root_path, "static", "uploads", m.filename))
        except Exception:
            pass
        db.session.delete(m)

    db.session.delete(p)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200
