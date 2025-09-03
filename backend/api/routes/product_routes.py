import os
from flask import Blueprint, jsonify, request, url_for, current_app
from werkzeug.utils import secure_filename

from backend.extensions import db
from backend.models import Product, ProductMedia, Category  # ponecháno

api_products = Blueprint("api_products", __name__, url_prefix="/api/products")


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


def _product_dict(product: Product):
    category_name = product.category.name if product.category else None
    category_group = product.category.group if product.category else None

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price_czk,
        "category_id": product.category_id,
        "category_name": category_name,
        "image_url": (
            url_for("static", filename=f"uploads/{product.image}", _external=True)
            if product.image else None
        ),
        "media": [
            url_for("static", filename=f"uploads/{m.filename}", _external=True)
            for m in (product.media or [])
        ],
        "categories": ([category_name] if category_name else []),
        "category_group": category_group,
    }


@api_products.get("/")
def get_products():
    items = Product.query.order_by(Product.id.desc()).all()
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
    category_id = request.form.get("category_id")

    if not name or not price_raw or not category_id:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        price = float(price_raw)
    except ValueError:
        return jsonify({"error": "Invalid price"}), 400

    p = Product(
        name=name,
        description=(description or None),
        price_czk=price,
        category_id=int(category_id),
    )

    image_file = request.files.get("image")
    if image_file and image_file.filename:
        filename = secure_filename(image_file.filename)
        upload_dir = os.path.join(current_app.root_path, "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        image_file.save(os.path.join(upload_dir, filename))
        p.image = filename

    db.session.add(p)
    db.session.flush()

    for mf in request.files.getlist("media"):
        if not mf or not mf.filename:
            continue
        mf_fn = secure_filename(mf.filename)
        upload_dir = os.path.join(current_app.root_path, "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        mf.save(os.path.join(upload_dir, mf_fn))
        media_type = _detect_media_type(mf_fn, mf.mimetype)
        db.session.add(ProductMedia(product_id=p.id, filename=mf_fn, media_type=media_type))

    db.session.commit()
    return jsonify(_product_dict(p)), 201


@api_products.put("/<int:product_id>")
def update_product(product_id: int):
    p = Product.query.get_or_404(product_id)

    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    price_raw = (request.form.get("price") or "").strip()
    category_id = request.form.get("category_id")

    if name:
        p.name = name
    p.description = (description or None)
    if price_raw:
        try:
            p.price_czk = float(price_raw)
        except ValueError:
            return jsonify({"error": "Invalid price"}), 400
    if category_id:
        p.category_id = int(category_id)

    image_file = request.files.get("image")
    if image_file and image_file.filename:
        filename = secure_filename(image_file.filename)
        upload_dir = os.path.join(current_app.root_path, "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        image_file.save(os.path.join(upload_dir, filename))
        p.image = filename

    for mf in request.files.getlist("media"):
        if not mf or not mf.filename:
            continue
        mf_fn = secure_filename(mf.filename)
        upload_dir = os.path.join(current_app.root_path, "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        mf.save(os.path.join(upload_dir, mf_fn))
        media_type = _detect_media_type(mf_fn, mf.mimetype)
        db.session.add(ProductMedia(product_id=p.id, filename=mf_fn, media_type=media_type))

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
