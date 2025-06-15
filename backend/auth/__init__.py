from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

from . import login_routes  # musí být zde, aby se routy načetly
