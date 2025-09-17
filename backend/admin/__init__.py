from flask import Blueprint

# Jeden jediný admin Blueprint pro /admin
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Importy ROUTŮ musí být až PO vytvoření blueprintu,
# aby se správně zaregistrovaly.
from . import routes            # dashboard + produkty (list/add/edit/delete)
from . import category_routes   # kategorie
from . import payments_routes   # platby
from . import sold_routes       # prodané
