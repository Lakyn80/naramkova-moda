import os
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import admin_bp
from extensions import db
from admin.models import Product, Category

# ------------------------------
# Admin Dashboard
# ------------------------------
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    product_count = Product.query.count()
    category_count = Category.query.count()
    return render_template("admin/dashboard.html",
                           user=current_user,
                           product_count=product_count,
                           category_count=category_count)

# ------------------------------
# Výpis produktů
# ------------------------------
@admin_bp.route("/admin/products")
@login_required
def list_products():
    products = Product.query.all()
    return render_template("admin/products/list.html", products=products)

# ------------------------------
# Přidání nového produktu
# ------------------------------
@admin_bp.route("/admin/products/add", methods=["GET", "POST"])
@login_required
def add_product():
    categories = Category.query.all()

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        price = request.form["price"]
        category_id = request.form.get("category_id")  # Nově
        image_file = request.files.get("image")

        try:
            price = float(price)
        except ValueError:
            flash("Cena musí být číslo.", "danger")
            return redirect(request.url)

        filename = None
        if image_file:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)

        new_product = Product(
            name=name,
            description=description,
            price_czk=price,
            image=filename,
            category_id=category_id if category_id else None,
        )

        db.session.add(new_product)
        db.session.commit()
        flash("Produkt byl úspěšně přidán.", "success")
        return redirect(url_for("admin.list_products"))

    return render_template("admin/products/add.html", categories=categories)
# ------------------------------
# Editace produktu
# ------------------------------
@admin_bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()

    if request.method == "POST":
        product.name = request.form["name"]
        product.description = request.form["description"]
        product.price_czk = request.form["price"]
        product.category_id = request.form.get("category_id") or None

        image_file = request.files.get("image")
        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            filepath = os.path.join(current_app.root_path, "static/uploads", filename)
            image_file.save(filepath)
            product.image = filename

        db.session.commit()
        flash("✅ Produkt byl úspěšně upraven.", "success")
        return redirect(url_for("admin.list_products"))

    return render_template("admin/products/edit.html", product=product, categories=categories)


# ------------------------------
# Smazání produktu
# ------------------------------
@admin_bp.route("/admin/products/delete/<int:product_id>")
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
