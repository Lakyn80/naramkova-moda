# 📁 backend/admin/__init__.py
from flask import Blueprint

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates"  # <- důležité pro načítání šablon z backend/admin/templates/
)

from . import routes
from . import category_routes
from . import payments_routes  # registrace admin /payments
