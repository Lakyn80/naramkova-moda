from flask import Blueprint, request, jsonify, current_app, url_for
from extensions import db
from admin.models import Product, Category, ProductMedia
import os
from werkzeug.utils import secure_filename

# ─── Blueprint pro API produktů ───────────────────────────────────────────────
api_products = Blueprint("api_products", __name__, url_prefix="/api/products")


# ─── Serializace: Produkt → JSON dict včetně médií ────────────────────────────
def product_to_dict(product):
    # Kategorie
    category = Category.query.get(product.category_id)
    category_name = category.name if category else None

    # Všechny přidružené soubory (media)
    media_list = [
        {
            "url": url_for("static", filename=f"uploads/{m.filename}", _external=True),
            "type": m.media_type
        }
        for m in product.media
    ]

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": float(product.price_czk),
        "image": url_for(
            "static", filename=f"uploads/{product.image}", _external=True
        ) if product.image else None,
        "media": media_list,
        "category_id": product.category_id,
        "category": {"name": category_name} if category_name else None,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat()
    }


# ─── GET /api/products/ – vrátí seznam všech produktů ─────────────────────────
@api_products.route("/", methods=["GET"])
def get_products():
    products = Product.query.all()
    return jsonify([product_to_dict(p) for p in products])


# ─── GET /api/products/<id> – detail jednoho produktu ─────────────────────────
@api_products.route("/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product_to_dict(product))


# ─── POST /api/products/ – vytvoření nového produktu ───────────────────────────
@api_products.route("/", methods=["POST"])
def create_product():
    data = request.form
    name        = data.get("name")
    description = data.get("description")
    price       = data.get("price")
    category_id = data.get("category_id")

    # 1) Validace povinných polí
    if not name or not price:
        return jsonify({"error": "Jméno a cena jsou povinné"}), 400
    try:
        price = float(price)
    except ValueError:
        return jsonify({"error": "Cena musí být číslo"}), 400

    # 2) Zpracování hlavního obrázku
    filename = None
    if "image" in request.files:
        img = request.files["image"]
        if img.filename:
            filename = secure_filename(img.filename)
            img.save(os.path.join(current_app.root_path, "static/uploads", filename))

    # 3) Vytvoření produktu (dosud bez médií)
    product = Product(
        name=name,
        description=description,
        price_czk=price,
        category_id=category_id or None,
        image=filename
    )
    db.session.add(product)
    db.session.flush()  # potřebujeme product.id pro media


    # 4) Zpracování dalších médií (více souborů)
    media_files = request.files.getlist("media")
    for mf in media_files:
        if mf and mf.filename:
            fn  = secure_filename(mf.filename)
            ext = os.path.splitext(fn)[1].lower()
            mf.save(os.path.join(current_app.root_path, "static/uploads", fn))

            # Určíme, zda je to obrázek nebo video
            if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                mtype = "image"
            elif ext in [".mp4", ".webm", ".mov"]:
                mtype = "video"
            else:
                continue  # ignorujeme neznámé formáty

            # Přidáme záznam do DB
            pm = ProductMedia(filename=fn, media_type=mtype, product_id=product.id)
            db.session.add(pm)

    # 5) Commit všeho do DB
    db.session.commit()
    return jsonify(product_to_dict(product)), 201


# ─── PUT /api/products/<id> – úprava existujícího produktu ────────────────────
@api_products.route("/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data    = request.form

    # 1) Aktualizace základních polí
    product.name        = data.get("name", product.name)
    product.description = data.get("description", product.description)
    product.price_czk   = data.get("price", product.price_czk)
    product.category_id = data.get("category_id", product.category_id)

    # 2) Změna hlavního obrázku (volitelně)
    if "image" in request.files:
        img = request.files["image"]
        if img.filename:
            fn = secure_filename(img.filename)
            img.save(os.path.join(current_app.root_path, "static/uploads", fn))
            product.image = fn

    db.session.flush()  # aby product.id zůstal v session

    # 3) Přidání dalších médií
    media_files = request.files.getlist("media")
    for mf in media_files:
        if mf and mf.filename:
            fn  = secure_filename(mf.filename)
            ext = os.path.splitext(fn)[1].lower()
            mf.save(os.path.join(current_app.root_path, "static/uploads", fn))

            mtype = "image" if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"] else "video"
            if mtype not in ["image", "video"]:
                continue

            pm = ProductMedia(filename=fn, media_type=mtype, product_id=product.id)
            db.session.add(pm)

    # 4) Commit změn
    db.session.commit()
    return jsonify(product_to_dict(product)), 200


# ─── DELETE /api/products/<id> – smazání produktu i médií ─────────────────────
@api_products.route("/<int:product_id>", methods=["DELETE"])
def delete_product_api(product_id):
    product = Product.query.get_or_404(product_id)

    # 1) Smažeme hlavní obrázek z disku
    if product.image:
        p = os.path.join(current_app.root_path, "static/uploads", product.image)
        if os.path.exists(p):
            os.remove(p)

    # 2) Smažeme všechna přidružená média z disku
    for m in product.media:
        mp = os.path.join(current_app.root_path, "static/uploads", m.filename)
        if os.path.exists(mp):
            os.remove(mp)

    # 3) Odstraníme z DB (cascade smaže ProductMedia)
    db.session.delete(product)
    db.session.commit()

    return jsonify({"message": "Produkt byl smazán."}), 200
