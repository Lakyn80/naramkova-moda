import os
import requests
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from . import admin_bp

# ✅ OPRAVENÉ IMPORTY MODELŮ A EXTENSION
from backend.admin.models import Product, Category, ProductMedia
from backend.extensions import db


# ─── Admin Dashboard ─────────────────────────────────────────────
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    product_count = Product.query.count()
    category_count = Category.query.count()
    return render_template(
        "admin/dashboard.html",
        user=current_user,
        product_count=product_count,
        category_count=category_count
    )


# ─── Výpis všech produktů ────────────────────────────────────────
@admin_bp.route("/admin/products")
@login_required
def list_products():
    products = Product.query.all()
    return render_template("admin/products/list.html", products=products)


# ─── Přidání nového produktu ─────────────────────────────────────
@admin_bp.route("/admin/products/add", methods=["GET", "POST"])
@login_required
def add_product():
    categories = Category.query.all()

    if request.method == "POST":
        data = {
            "name": request.form["name"],
            "description": request.form.get("description"),
            "price": request.form["price"],
            "category_id": request.form.get("category_id") or ""
        }

        files = []

        image_file = request.files.get("image")
        if image_file and image_file.filename:
            img_fn = secure_filename(image_file.filename)
            files.append(("image", (img_fn, image_file.stream, image_file.mimetype)))

        media_files = request.files.getlist("media")
        for mf in media_files:
            if mf and mf.filename:
                mf_fn = secure_filename(mf.filename)
                files.append(("media", (mf_fn, mf.stream, mf.mimetype)))

        api_url = request.host_url.rstrip("/") + "/api/products/"
        response = requests.post(url=api_url, data=data, files=files)

        if response.status_code == 201:
            flash("✅ Produkt byl úspěšně přidán přes API.", "success")
            return redirect(url_for("admin.list_products"))
        else:
            flash("❌ Chyba při přidávání produktu přes API.", "danger")
            return redirect(request.url)

    return render_template("admin/products/add.html", categories=categories)


# ─── Úprava produktu ─────────────────────────────────────────────
@admin_bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()

    if request.method == "POST":
        data = {
            "name": request.form["name"],
            "description": request.form.get("description"),
            "price": request.form["price"],
            "category_id": request.form.get("category_id") or ""
        }

        files = []

        image_file = request.files.get("image")
        if image_file and image_file.filename:
            img_fn = secure_filename(image_file.filename)
            files.append(("image", (img_fn, image_file.stream, image_file.mimetype)))

        media_files = request.files.getlist("media")
        for mf in media_files:
            if mf and mf.filename:
                mf_fn = secure_filename(mf.filename)
                files.append(("media", (mf_fn, mf.stream, mf.mimetype)))

        api_url = request.host_url.rstrip("/") + f"/api/products/{product_id}"
        response = requests.put(url=api_url, data=data, files=files)

        if response.status_code == 200:
            flash("✅ Produkt byl upraven přes API.", "success")
            return redirect(url_for("admin.list_products"))
        else:
            flash("❌ Chyba při úpravě produktu přes API.", "danger")
            return redirect(request.url)

    return render_template(
        "admin/products/edit.html",
        product=product,
        categories=categories
    )


# ─── Smazání produktu ────────────────────────────────────────────
@admin_bp.route("/admin/products/delete/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    api_url = request.host_url.rstrip("/") + f"/api/products/{product_id}"
    response = requests.delete(url=api_url)

    if response.status_code == 200:
        flash("🗑️ Produkt byl smazán přes API.", "info")
    else:
        flash("❌ Chyba při mazání produktu přes API.", "danger")

    return redirect(url_for("admin.list_products"))


# ─── Smazání obrázku nebo videa ─────────────────────────────────
@admin_bp.route("/admin/media/delete/<int:media_id>", methods=["POST"])
@login_required
def delete_product_media(media_id):
    media = ProductMedia.query.get_or_404(media_id)
    product_id = media.product_id

    file_path = os.path.join(current_app.root_path, "static/uploads", media.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(media)
    db.session.commit()

    flash("🗑️ Médium bylo smazáno.", "info")
    return redirect(url_for("admin.edit_product", product_id=product_id))