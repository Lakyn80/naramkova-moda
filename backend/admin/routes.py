import os
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import admin_bp
from extensions import db
from admin.models import Product

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("admin/dashboard.html", user=current_user)

# ─────────────────────────────────────────────────────────────────────────────
# VÝPIS PRODUKTŮ
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route("/admin/products")
@login_required
def list_products():
    products = Product.query.all()
    return render_template("admin/products/list.html", products=products)

# ─────────────────────────────────────────────────────────────────────────────
# PŘIDÁNÍ NOVÉHO PRODUKTU
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route("/admin/products/add", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        price = request.form["price"]
        image_file = request.files.get("image")

        try:
            price = float(price)
        except ValueError:
            flash("Cena musí být číslo.", "danger")
            return redirect(url_for("admin.add_product"))

        filename = None
        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            image_file.save(upload_path)

        product = Product(name=name, description=description, price_czk=price, image=filename)
        db.session.add(product)
        db.session.commit()
        flash("Produkt přidán!", "success")
        return redirect(url_for("admin.list_products"))

    return render_template("admin/products/add.html")

# ─────────────────────────────────────────────────────────────────────────────
# EDITACE PRODUKTU
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route("/admin/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        product.name = request.form["name"]
        product.description = request.form["description"]
        price = request.form["price"]
        image_file = request.files.get("image")

        try:
            product.price_czk = float(price)
        except ValueError:
            flash("Cena musí být číslo.", "danger")
            return redirect(url_for("admin.edit_product", product_id=product.id))

        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            image_file.save(upload_path)
            product.image = filename

        db.session.commit()
        flash("Produkt upraven.", "success")
        return redirect(url_for("admin.list_products"))

    return render_template("admin/products/edit.html", product=product)

# ─────────────────────────────────────────────────────────────────────────────
# MAZÁNÍ PRODUKTU
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route("/admin/products/delete/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    if product.image:
        image_path = os.path.join(current_app.config["UPLOAD_FOLDER"], product.image)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(product)
    db.session.commit()
    flash("Produkt byl smazán.", "success")
    return redirect(url_for("admin.list_products"))
