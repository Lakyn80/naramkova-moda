from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="templates")

# VŠECHNY importy
from . import routes            # dashboard + produkty
from . import category_routes   # kategorie
from . import payments_routes   # platby
from . import sold_routes       # prodané
