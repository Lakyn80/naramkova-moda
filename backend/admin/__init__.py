from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

from . import routes
from . import category_routes
from . import payments_routes   # ✅ jen tento pro platby
from . import sold_routes
