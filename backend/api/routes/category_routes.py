from __future__ import annotations

from flask import Blueprint, request, jsonify
from backend.extensions import db
from backend.models import Category

api_categories = Blueprint("api_categories", __name__, url_prefix="/api/categories")


def _cat_to_dict(c: Category) -> dict:
    # Vrací jak původní 'group', tak alias 'category' (kvůli FE/administraci bez migrace DB)
    return {
        "id": c.id,
        "name": c.name,
        "description": getattr(c, "description", None),
        "group": getattr(c, "group", None),
        "category": getattr(c, "group", None),  # alias
    }


def _get_payload() -> dict:
    return request.get_json(silent=True) or request.form or {}


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


@api_categories.post("/")
def create_category():
    data = _get_payload()
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip() or None

    # přijmi group i category (alias)
    group_val = (data.get("group") or data.get("category") or "").strip() or None

    if not name:
        return jsonify({"error": "Missing 'name'"}), 400

    c = Category(name=name, description=description, group=group_val)
    db.session.add(c)
    db.session.commit()
    return jsonify(_cat_to_dict(c)), 201


@api_categories.put("/<int:category_id>")
def update_category(category_id: int):
    c = Category.query.get_or_404(category_id)
    data = _get_payload()

    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "Invalid 'name'"}), 400
        c.name = name

    if "description" in data:
        c.description = (data.get("description") or "").strip() or None

    if "group" in data or "category" in data:
        c.group = (data.get("group") or data.get("category") or "").strip() or None

    db.session.commit()
    return jsonify(_cat_to_dict(c)), 200


@api_categories.delete("/<int:category_id>")
def delete_category(category_id: int):
    c = Category.query.get_or_404(category_id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"ok": True}), 200
