import os
import requests
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from backend.admin import admin_bp
from backend.extensions import db
from backend.admin.models import Product, Category, ProductMedia
from werkzeug.utils import secure_filename


def _file_tuple(fs):
    """Vrátí (filename, fileobj, mimetype) s fallbackem."""
    fn = secure_filename(fs.filename)
    fobj = getattr(fs, "stream", None) or fs
    ctype = fs.mimetype or "application/octet-stream"
    return (fn, fobj, ctype)


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    product_count = Product.query.count()
    category_count = Category.query.count()
    return render_template(
        "admin/dashboard.html",
        user=current_user,
        product_count=product_count,
        category_count=category_count,
    )


@admin_bp.route("/products")
@login_required
def list_products():
    products = Product.query.all()
    return render_template("admin/products/list.html", products=products)


@admin_bp.route("/products/add", methods=["GET", "POST"])
@login_required
def add_product():
    categories = Category.query.order_by(Category.name.asc()).all()
    category_labels = {c.id: f"{(c.group or '—')} — {c.name}" for c in categories}

    if request.method == "POST":
        data = {
            "name": request.form.get("name", ""),
            "description": request.form.get("description") or "",
            "price": request.form.get("price", ""),
            "category_id": request.form.get("category_id") or "",
        }

        files = []
        image_file = request.files.get("image")
        if image_file and image_file.filename:
            files.append(("image", _file_tuple(image_file)))

        media_files = request.files.getlist("media")
        for mf in media_files or []:
            if mf and mf.filename:
                files.append(("media", _file_tuple(mf)))

        api_url = request.host_url.rstrip("/") + "/api/products/"
        try:
            response = requests.post(url=api_url, data=data, files=files)
        except Exception as e:
            flash(f"❌ Chyba volání API: {e}", "danger")
            return redirect(request.url)

        if response.status_code == 201:
            flash("✅ Produkt byl úspěšně přidán přes API.", "success")
            return redirect(url_for("admin.list_products"))
        else:
            flash("❌ Chyba při přidávání produktu přes API.", "danger")
            return redirect(request.url)

    return render_template("admin/products/add.html", categories=categories, category_labels=category_labels)


@admin_bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id: int):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.name.asc()).all()
    category_labels = {c.id: f"{(c.group or '—')} — {c.name}" for c in categories}

    if request.method == "POST":
        data = {
            "name": request.form.get("name", ""),
            "description": request.form.get("description") or "",
            "price": request.form.get("price", ""),
            "category_id": request.form.get("category_id") or "",
        }

        files = []
        image_file = request.files.get("image")
        if image_file and image_file.filename:
            files.append(("image", _file_tuple(image_file)))

        media_files = request.files.getlist("media")
        for mf in media_files or []:
            if mf and mf.filename:
                files.append(("media", _file_tuple(mf)))

        api_url = request.host_url.rstrip("/") + f"/api/products/{product_id}"
        try:
            response = requests.put(url=api_url, data=data, files=files)
        except Exception as e:
            flash(f"❌ Chyba volání API: {e}", "danger")
            return redirect(request.url)

        if response.status_code == 200:
            flash("✅ Produkt byl upraven přes API.", "success")
            return redirect(url_for("admin.list_products"))
        else:
            flash("❌ Chyba při úpravě produktu přes API.", "danger")
            return redirect(request.url)

    return render_template("admin/products/edit.html", product=product, categories=categories, category_labels=category_labels)


@admin_bp.route("/products/delete/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id: int):
    api_url = request.host_url.rstrip("/") + f"/api/products/{product_id}"
    try:
        response = requests.delete(url=api_url)
    except Exception as e:
        flash(f"❌ Chyba volání API: {e}", "danger")
        return redirect(url_for("admin.list_products"))

    if response.status_code == 200:
        flash("🗑️ Produkt byl smazán přes API.", "info")
    else:
        flash("❌ Chyba při mazání produktu přes API.", "danger")

    return redirect(url_for("admin.list_products"))
