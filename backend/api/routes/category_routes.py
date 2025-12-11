from __future__ import annotations

import re
import unicodedata

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import selectinload

from backend.api.routes.product_routes import _product_dict
from backend.extensions import db
from backend.models import Category, Product, ProductVariant

api_categories = Blueprint("api_categories", __name__, url_prefix="/api/categories")


def _cat_to_dict(c: Category) -> dict:
    # Vrací jak původní 'group', tak alias 'category' (kvůli FE/administraci bez migrace DB)
    return {
        "id": c.id,
        "name": c.name,
        "description": getattr(c, "description", None),
        "slug": getattr(c, "slug", None),
        "group": getattr(c, "group", None),
        "category": getattr(c, "group", None),  # alias
    }


def _get_payload() -> dict:
    return request.get_json(silent=True) or request.form or {}


def _slugify(val: str) -> str:
    raw = (val or "").strip().lower()
    if not raw:
        return "kategorie"
    try:
        normalized = unicodedata.normalize("NFKD", raw)
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    except Exception:
        normalized = raw
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized or "kategorie"


def _unique_slug(base: str, exclude_id: int | None = None) -> str:
    slug = base or "kategorie"
    candidate = slug
    suffix = 1
    while True:
        q = Category.query.filter(Category.slug == candidate)
        if exclude_id:
            q = q.filter(Category.id != exclude_id)
        if not q.first():
            return candidate
        suffix += 1
        candidate = f"{slug}-{suffix}"


@api_categories.get("/")
def list_categories():
    q = Category.query
    # filtr může přijít jako group= nebo category=
    group = request.args.get("group") or request.args.get("category")
    if group:
        q = q.filter(Category.group == group)
    items = q.order_by(Category.name.asc()).all()
    return jsonify([_cat_to_dict(c) for c in items]), 200


@api_categories.get("/<int:category_id>")
def get_category(category_id: int):
    c = Category.query.get_or_404(category_id)
    return jsonify(_cat_to_dict(c)), 200


@api_categories.get("/<string:slug>")
def get_category_by_slug(slug: str):
    c = Category.query.filter(Category.slug == str(slug).strip()).first()
    if not c:
        return jsonify({"error": "Category not found"}), 404

    products_q = (
        Product.query.options(
            selectinload(Product.media),
            selectinload(Product.category),
            selectinload(Product.variants).selectinload(ProductVariant.media),
        )
        .filter(Product.category_id == c.id, Product.stock > 0)
    )

    wrist_size = (request.args.get("wrist_size") or "").strip()
    if wrist_size:
        products_q = (
            products_q.join(ProductVariant, ProductVariant.product_id == Product.id)
            .filter(ProductVariant.wrist_size == wrist_size)
            .distinct()
        )

    products = products_q.order_by(Product.id.desc()).all()
    return jsonify({
        "category": _cat_to_dict(c),
        "products": [_product_dict(p) for p in products],
    }), 200


@api_categories.post("/")
def create_category():
    data = _get_payload()
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip() or None

    # přijmi group i category (alias)
    group_val = (data.get("group") or data.get("category") or "").strip() or None
    slug_raw = (data.get("slug") or "").strip()

    if not name:
        return jsonify({"error": "Missing 'name'"}), 400

    slug_val = _unique_slug(_slugify(slug_raw or name))

    c = Category(name=name, description=description, group=group_val, slug=slug_val)
    db.session.add(c)
    db.session.commit()
    return jsonify(_cat_to_dict(c)), 201


@api_categories.put("/<int:category_id>")
def update_category(category_id: int):
    c = Category.query.get_or_404(category_id)
    data = _get_payload()

    new_name = None
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "Invalid 'name'"}), 400
        c.name = name
        new_name = name

    if "description" in data:
        c.description = (data.get("description") or "").strip() or None

    if "group" in data or "category" in data:
        c.group = (data.get("group") or data.get("category") or "").strip() or None

    if "slug" in data or (not getattr(c, "slug", None) and new_name):
        slug_raw = (data.get("slug") or "").strip()
        slug_source = slug_raw or new_name or c.name
        c.slug = _unique_slug(_slugify(slug_source), exclude_id=c.id)

    db.session.commit()
    return jsonify(_cat_to_dict(c)), 200


@api_categories.delete("/<int:category_id>")
def delete_category(category_id: int):
    c = Category.query.get_or_404(category_id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"ok": True}), 200
