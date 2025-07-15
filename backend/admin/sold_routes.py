from flask import Blueprint, render_template
from backend.extensions import db
from backend.admin.models import SoldProduct
from flask_login import login_required

sold_bp = Blueprint("sold", __name__)

@sold_bp.route("/admin/sold")
@login_required
def sold_products():
    sold = SoldProduct.query.order_by(SoldProduct.sold_at.desc()).all()
    return render_template("admin/sold/list.html", sold_products=sold)
