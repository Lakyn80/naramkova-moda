from flask import Blueprint, request, jsonify, current_app
from extensions import db
from admin.models import Product, Category
import os
from werkzeug.utils import secure_filename
from flask import url_for

api_products = Blueprint("api_products", __name__, url_prefix="/api/products")

# Pomocná funkce pro převod produktu na slovník
def product_to_dict(product):
    image_url = (
        url_for("static", filename=f"uploads/{product.image}", _external=True)
        if product.image else None
    )
    category = Category.query.get(product.category_id)
    category_name = category.name if category else None

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": float(product.price_czk),
        "image": image_url,  # ← Tady je změna
        "category_id": product.category_id,
        "category": {"name": category_name} if category_name else None,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat()
    }

# ---------------------------
# Získání všech produktů
# ---------------------------
@api_products.route("/", methods=["GET"])
def get_products():
    products = Product.query.all()
    return jsonify([product_to_dict(p) for p in products])

# ---------------------------
# Získání konkrétního produktu
# ---------------------------
@api_products.route("/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product_to_dict(product))

# ---------------------------
# Přidání nového produktu
# ---------------------------
@api_products.route("/", methods=["POST"])
def create_product():
    data = request.form
    name = data.get("name")
    description = data.get("description")
    price = data.get("price")
    category_id = data.get("category_id")

    if not name or not price:
        return jsonify({"error": "Jméno a cena jsou povinné"}), 400

    try:
        price = float(price)
    except ValueError:
        return jsonify({"error": "Cena musí být číslo"}), 400

    filename = None
    if "image" in request.files:
        image_file = request.files["image"]
        if image_file.filename != "":
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(current_app.root_path, "static/uploads", filename)
            image_file.save(image_path)

    product = Product(
        name=name,
        description=description,
        price_czk=price,
        category_id=category_id or None,
        image=filename
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(product_to_dict(product)), 201

# ---------------------------
# Úprava produktu
# ---------------------------
@api_products.route("/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.form
    product.name = data.get("name", product.name)
    product.description = data.get("description", product.description)
    product.price_czk = data.get("price", product.price_czk)
    product.category_id = data.get("category_id", product.category_id)

    if "image" in request.files:
        image_file = request.files["image"]
        if image_file.filename != "":
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(current_app.root_path, "static/uploads", filename)
            image_file.save(image_path)
            product.image = filename

    db.session.commit()
    return jsonify(product_to_dict(product)), 200

# ---------------------------
# Smazání produktu
# ---------------------------
@api_products.route("/<int:product_id>", methods=["DELETE"])
def delete_product_api(product_id):
    product = Product.query.get_or_404(product_id)

    if product.image:
        image_path = os.path.join(current_app.root_path, "static/uploads", product.image)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Produkt byl smazán."}), 200
