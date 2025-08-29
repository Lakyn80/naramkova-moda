# backend/admin/__init__.py
from flask import Blueprint

# Blueprint pro admin
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Naimportuj moduly, které registrují routy do admin_bp
from . import routes          # dashboard + produkty
from . import category_routes # kategorie
from . import payments_routes # platby v adminu
from . import sold_routes     # prodané produkty + faktury


