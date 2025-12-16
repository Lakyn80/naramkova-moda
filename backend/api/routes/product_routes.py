import json
import os
import uuid
from flask import Blueprint, jsonify, request, url_for, current_app
from werkzeug.utils import secure_filename

from backend.extensions import db
from backend.models import Product, ProductMedia, ProductVariant, ProductVariantMedia, Category
from sqlalchemy.orm import selectinload

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


def _parse_variants_from_request():
    """
    Načte varianty z requestu.
    Podporuje:
      - JSON payload: {"variants": [{variant_name, wrist_size, image}]}
      - form-data pole 'variants' s JSON stringem
      - form-data pole variant_name[] / variant_wrist_size[] / variant_image[]
    Vrací (variants_list, explicit_flag).
    explicit_flag říká, zda byl klientem variantový payload poskytnut (i prázdný),
    abychom mohli u PUT rozhodnout, zda varianty přepsat.
    """
    variants: list[dict] = []
    explicit = False

    # --- ADD PRODUCT: ignoruj všechny existing_* (Chrome posílá starý multipart bordel) ---
    if request.path.endswith("/products/add"):
        form = request.form.to_dict(flat=False)
        for key in list(form.keys()):
            if key.startswith("variant_image_existing"):
                form[key] = []

    def _to_int(val, default=None):
        try:
            return int(val)
        except (TypeError, ValueError):
            return default
    def _to_price(val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    is_multipart = (request.content_type or "").lower().startswith("multipart/form-data")

    # Pokud jde o multipart (admin formulář), ignoruj JSON payload,
    # abychom se vyhnuli zdvojení variant z více zdrojů.
    if not is_multipart:
        payload_json = request.get_json(silent=True) if request.is_json else None
        if isinstance(payload_json, dict) and "variants" in payload_json:
            explicit = True
            raw_list = payload_json.get("variants") or []
            if isinstance(raw_list, list):
                for v in raw_list:
                    if not isinstance(v, dict):
                        continue
                    variants.append(
                        {
                            "variant_name": (v.get("variant_name") or v.get("name") or "").strip() or None,
                            "wrist_size": (v.get("wrist_size") or "").strip() or None,
                            "description": (v.get("description") or "").strip() or None,
                            "price_czk": _to_price(v.get("price_czk") or v.get("price")),
                            "stock": _to_int(v.get("stock"), default=0),
                            "image": (v.get("image") or "").strip() or None,
                        }
                    )

    raw_form_variants = request.form.get("variants")
    if not is_multipart and raw_form_variants is not None:
        explicit = True
        try:
            parsed = json.loads(raw_form_variants) or []
            if isinstance(parsed, list):
                for v in parsed:
                    if not isinstance(v, dict):
                        continue
                    variants.append(
                        {
                            "variant_name": (v.get("variant_name") or v.get("name") or "").strip() or None,
                            "wrist_size": (v.get("wrist_size") or "").strip() or None,
                            "description": (v.get("description") or "").strip() or None,
                            "price_czk": _to_price(v.get("price_czk") or v.get("price")),
                            "stock": _to_int(v.get("stock"), default=0),
                            "image": (v.get("image") or "").strip() or None,
                        }
                    )
        except Exception:
            # pokud JSON parsování selže, prostě ignoruj
            pass

    names = request.form.getlist("variant_name[]")
    wrists = request.form.getlist("variant_wrist_size[]")
    stocks = request.form.getlist("variant_stock[]")
    files = request.files.getlist("variant_image[]")
    descriptions = request.form.getlist("variant_description[]")
    prices = request.form.getlist("variant_price[]")
    if names or wrists or files:
        explicit = True

    # Pokud dorazí pole z formuláře, ignoruj předchozí JSON/form "variants" a začni čistě,
    # aby se nenačetly duplicitní varianty ze dvou zdrojů.
    if names or wrists or stocks or descriptions or prices or files:
        variants = []

    # Počet řádků odvozujeme primárně z textových polí (řádky formuláře),
    # aby se nevytvářely duplicitní varianty jen kvůli počtu file-inputů.
    max_len = max(len(names), len(wrists), len(stocks), len(descriptions), len(prices))
    # Pokud nejsou textová pole, ale přišly soubory (okrajový případ), vezmi počet souborů.
    if max_len == 0 and files:
        max_len = len(files)
    existing_main_list = request.form.getlist("variant_image_existing[]")
    for i in range(max_len):
        n = names[i] if i < len(names) else ""
        w = wrists[i] if i < len(wrists) else ""
        s_raw = stocks[i] if i < len(stocks) else None
        s_val = _to_int(s_raw, default=0)
        desc = descriptions[i] if i < len(descriptions) else None
        price_val = prices[i] if i < len(prices) else None
        f = files[i] if i < len(files) else None
        has_file = bool(f and getattr(f, "filename", None))
        existing_main = existing_main_list[i] if i < len(existing_main_list) else None
        extra_files = request.files.getlist(f"variant_image_multi_{i}[]")
        extra_existing = request.form.getlist(f"variant_image_existing_multi_{i}[]")
        # Variantu vytvoříme jen pokud má nějaká hlavní data (název/velikost/hlavní foto/cena)
        # Samotné "další fotky" ji už nespustí.
        if not (n or w or has_file or existing_main or price_val):
            continue
        variants.append(
            {
                "variant_name": (n or None),
                "wrist_size": (w or None),
                "description": (desc or None),
                "price_czk": _to_price(price_val),
                "stock": s_val if s_val is not None else 0,
                "image_file": f if has_file else None,
                "existing_image": (existing_main or None),
                "extra_files": [ef for ef in extra_files if getattr(ef, "filename", None)],
                "existing_extra": [ee for ee in extra_existing if ee],
            }
        )

    return variants, explicit


def _variant_media_dict(m: ProductVariantMedia):
    return {
        "id": m.id,
        "image": m.filename,
        "image_url": f"/static/uploads/{m.filename}" if m.filename else None,
    }


def _variant_dict(variant: ProductVariant):
    return {
        "id": variant.id,
        "variant_name": variant.variant_name,
        "wrist_size": variant.wrist_size,
        "description": variant.description,
        "price_czk": float(variant.price_czk) if variant.price_czk is not None else None,
        "stock": variant.stock,
        "image": variant.image,
        "image_url": f"/static/uploads/{variant.image}" if variant.image else None,
        "media": [_variant_media_dict(m) for m in (variant.media or [])],
    }


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
        "category_slug": getattr(product.category, "slug", None),
        # Use relative URLs so frontend can prefix with its own origin/port
        "image_url": f"/static/uploads/{product.image}" if product.image else None,
        "media": [f"/static/uploads/{m.filename}" for m in (product.media or [])],
        "categories": ([category_name] if category_name else []),
        "category_group": category_group,
        "variants": [_variant_dict(v) for v in (product.variants or [])],
    }


# ========================= Endpoints =========================

@api_products.get("/")
def get_products():
    # ✅ filtrujeme jen produkty se stock > 0
    items = (
        Product.query.options(
            selectinload(Product.media),
            selectinload(Product.category),
            selectinload(Product.variants).selectinload(ProductVariant.media),
        )
        .filter(Product.stock > 0)
        .order_by(Product.id.desc())
        .all()
    )
    return jsonify([_product_dict(p) for p in items]), 200


@api_products.get("/<int:product_id>")
def get_product(product_id: int):
    p = (
        Product.query.options(
            selectinload(Product.media),
            selectinload(Product.category),
            selectinload(Product.variants).selectinload(ProductVariant.media),
        )
        .filter(Product.id == product_id)
        .first_or_404()
    )
    return jsonify(_product_dict(p)), 200


@api_products.post("/")
def add_product():
    data = request.form if request.form else (request.get_json(silent=True) or {})

    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    price_raw = str(data.get("price") or data.get("price_czk") or "").strip()
    stock_raw = str(data.get("stock") or "").strip()
    category_id = data.get("category_id")

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

    try:
        category_id_int = int(category_id)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid category_id"}), 400

    p = Product(
        name=name,
        description=(description or None),
        price_czk=price,
        stock=stock,  # ✅ uložíme počet kusů
        category_id=category_id_int,
    )

    # --- Hlavní obrázek: vždy normalizujeme do WebP ---
    image_file = request.files.get("image")
    if image_file and image_file.filename:
        # Uloží se jako <uuid>.webp (nebo originál, když PIL není)
        normalized = _process_and_save_image(image_file)
        p.image = normalized

    db.session.add(p)
    db.session.flush()

    variants_payload, _ = _parse_variants_from_request()

    def _has_variant_data(v: dict) -> bool:
        core_filled = any(
            [
                bool((v.get("variant_name") or "").strip()),
                bool((v.get("wrist_size") or "").strip()),
                bool(v.get("image") or v.get("existing_image") or v.get("image_file")),
                v.get("price_czk") is not None,
            ]
        )
        if not core_filled:
            return False
        # U nového produktu ignoruj varianty, které nesou jen existing_image (pozůstatek starých dat)
        if v.get("existing_image") and not v.get("image_file"):
            return False
        return True

    def _dedupe_variants(items: list[dict]) -> list[dict]:
        seen = set()
        result = []
        for v in items:
            key = (
                (v.get("variant_name") or "").strip().lower(),
                (v.get("wrist_size") or "").strip().lower(),
                (v.get("description") or "").strip().lower(),
                float(v["price_czk"]) if v.get("price_czk") is not None else None,
                int(v.get("stock")) if v.get("stock") is not None else None,
                (v.get("existing_image") or v.get("image") or "").strip().lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            result.append(v)
        return result

    variants_payload = _dedupe_variants([v for v in variants_payload if _has_variant_data(v)])
    for idx, variant in enumerate(variants_payload):
        img_name = variant.get("image") or None
        if variant.get("image_file"):
            img_name = _process_and_save_image(variant["image_file"])

        if not (variant.get("variant_name") or variant.get("wrist_size") or img_name):
            continue

        v_obj = ProductVariant(
            product_id=p.id,
            variant_name=variant.get("variant_name"),
            wrist_size=variant.get("wrist_size"),
            description=variant.get("description"),
            price_czk=variant.get("price_czk"),
            stock=variant.get("stock") or 0,
            image=img_name,
        )
        db.session.add(v_obj)
        for ef in variant.get("extra_files") or []:
            saved = _process_and_save_image(ef)
            db.session.add(ProductVariantMedia(variant=v_obj, filename=saved))

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

    data = request.form if request.form else (request.get_json(silent=True) or {})
    clear_variants_flag = request.form.get("clear_variants") == "1"

    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    price_raw = str(data.get("price") or data.get("price_czk") or "").strip()
    stock_raw = str(data.get("stock") or "").strip()
    category_id = data.get("category_id")
    variants_payload, variants_explicit = _parse_variants_from_request()

    if clear_variants_flag:
        variants_payload = []
        variants_explicit = True

    def _has_variant_data(v: dict) -> bool:
        core_filled = any(
            [
                bool((v.get("variant_name") or "").strip()),
                bool((v.get("wrist_size") or "").strip()),
                bool(v.get("image") or v.get("existing_image") or v.get("image_file")),
                v.get("price_czk") is not None,
            ]
        )
        if not core_filled:
            return False
        return True

    def _dedupe_variants(items: list[dict]) -> list[dict]:
        seen = set()
        result = []
        for v in items:
            key = (
                (v.get("variant_name") or "").strip().lower(),
                (v.get("wrist_size") or "").strip().lower(),
                (v.get("description") or "").strip().lower(),
                float(v["price_czk"]) if v.get("price_czk") is not None else None,
                int(v.get("stock")) if v.get("stock") is not None else None,
                (v.get("existing_image") or v.get("image") or "").strip().lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            result.append(v)
        return result

    variants_payload = _dedupe_variants([v for v in variants_payload if _has_variant_data(v)])

    def _has_variant_data(v: dict) -> bool:
        return any(
            [
                bool((v.get("variant_name") or "").strip()),
                bool((v.get("wrist_size") or "").strip()),
                bool(v.get("image") or v.get("existing_image") or v.get("image_file")),
                bool((v.get("description") or "").strip()),
                v.get("price_czk") is not None,
            ]
        )

    variants_payload = [v for v in variants_payload if _has_variant_data(v)]

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
        try:
            p.category_id = int(category_id)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid category_id"}), 400

    if variants_explicit:
        old_variants = list(p.variants or [])
        existing_files: set[str] = set()
        for ov in old_variants:
            if ov.image:
                existing_files.add(ov.image)
            for mv in list(ov.media or []):
                if mv.filename:
                    existing_files.add(mv.filename)

        p.variants.clear()
        new_files: set[str] = set()

        for variant in variants_payload:
            img_name = variant.get("image") or variant.get("existing_image") or None
            if variant.get("image_file"):
                img_name = _process_and_save_image(variant["image_file"])

            if not (variant.get("variant_name") or variant.get("wrist_size") or img_name):
                continue

            if img_name:
                new_files.add(img_name)

            extra_existing = variant.get("existing_extra") or []
            extra_saved: list[str] = []
            for ef in variant.get("extra_files") or []:
                saved = _process_and_save_image(ef)
                extra_saved.append(saved)

            new_files.update(extra_existing)
            new_files.update(extra_saved)

            v_obj = ProductVariant(
                product_id=p.id,
                variant_name=variant.get("variant_name"),
                wrist_size=variant.get("wrist_size"),
                description=variant.get("description"),
                price_czk=variant.get("price_czk"),
                stock=variant.get("stock") or 0,
                image=img_name,
            )
            db.session.add(v_obj)

            for fn in extra_existing:
                db.session.add(ProductVariantMedia(variant=v_obj, filename=fn))
            for fn in extra_saved:
                db.session.add(ProductVariantMedia(variant=v_obj, filename=fn))

        # remove unused old files
        for fname in existing_files - new_files:
            try:
                os.remove(os.path.join(current_app.root_path, "static", "uploads", fname))
            except Exception:
                pass

    # --- Hlavní obrázek: při změně normalizovat do WebP ---
    image_file = request.files.get("image")
    if image_file and image_file.filename:
        old_image = p.image
        normalized = _process_and_save_image(image_file)
        p.image = normalized
        if old_image and old_image != normalized:
            try:
                os.remove(os.path.join(current_app.root_path, "static", "uploads", old_image))
            except Exception:
                pass

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

    for v in list(p.variants or []):
        if v.image:
            try:
                os.remove(os.path.join(current_app.root_path, "static", "uploads", v.image))
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
