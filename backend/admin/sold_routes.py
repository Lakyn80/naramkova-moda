from flask import render_template
from flask_login import login_required
from backend.admin.models import SoldProduct
from backend.admin import admin_bp

@admin_bp.route("/sold")
@login_required
def sold_products():
    sold = SoldProduct.query.order_by(SoldProduct.sold_at.desc()).all()
    return render_template("admin/sold/list.html", sold_products=sold)
