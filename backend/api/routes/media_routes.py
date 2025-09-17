# backend/api/routes/media_routes.py

from flask import Blueprint, jsonify, current_app
from backend.extensions import db
from backend.admin.models import ProductMedia
import os

api_media = Blueprint("api_media", __name__, url_prefix="/api/media")

@api_media.route("/<int:media_id>", methods=["DELETE"])
def delete_media(media_id):
    media = ProductMedia.query.get_or_404(media_id)

    # Smazání souboru ze složky uploads
    file_path = os.path.join(current_app.root_path, "static", "uploads", media.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Smazání z databáze
    db.session.delete(media)
    db.session.commit()

    return jsonify({"message": "Médium bylo úspěšně smazáno."}), 200
