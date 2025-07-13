from flask import Blueprint, jsonify, request
from extensions import db
from admin.models import Category

api_categories = Blueprint("api_categories", __name__, url_prefix="/api/categories")

# Pomocná funkce na převod do dict
def category_to_dict(category):
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description
    }

# GET /api/categories – seznam všech kategorií
@api_categories.route("/", methods=["GET"])
def get_categories():
    categories = Category.query.all()
    return jsonify([category_to_dict(cat) for cat in categories])

# GET /api/categories/<id> – detail kategorie
@api_categories.route("/<int:category_id>", methods=["GET"])
def get_category(category_id):
    category = Category.query.get_or_404(category_id)
    return jsonify(category_to_dict(category))

# POST /api/categories – vytvoření nové kategorie
@api_categories.route("/", methods=["POST"])
def create_category():
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")

    if not name:
        return jsonify({"error": "Název je povinný"}), 400

    category = Category(name=name, description=description)
    db.session.add(category)
    db.session.commit()
    return jsonify(category_to_dict(category)), 201

# PUT /api/categories/<id> – úprava kategorie
@api_categories.route("/<int:category_id>", methods=["PUT"])
def update_category(category_id):
    category = Category.query.get_or_404(category_id)
    data = request.get_json()

    category.name = data.get("name", category.name)
    category.description = data.get("description", category.description)

    db.session.commit()
    return jsonify(category_to_dict(category)), 200

# DELETE /api/categories/<id> – smazání
@api_categories.route("/<int:category_id>", methods=["DELETE"])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Kategorie byla smazána."}), 200
