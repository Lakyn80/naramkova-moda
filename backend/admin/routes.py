import os
import requests
from flask import (
    render_template,  # vykreslení HTML šablon
    request,          # data z HTTP požadavků
    redirect,         # přesměrování na jinou URL
    url_for,          # generování URL pro endpointy
    flash,            # zobrazení flash zpráv v UI
    current_app       # přístup k aplikaci a její konfiguraci
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# Blueprint pro admin část
from . import admin_bp

# SQLAlchemy modely
from admin.models import Product, Category, ProductMedia
from extensions import db


# ─── Admin Dashboard ─────────────────────────────────────────────────────────
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    """
    Dashboard zobrazující počet produktů a kategorií.
    """
    product_count = Product.query.count()
    category_count = Category.query.count()
    return render_template(
        "admin/dashboard.html",
        user=current_user,
        product_count=product_count,
        category_count=category_count
    )


# ─── Výpis všech produktů ────────────────────────────────────────────────────
@admin_bp.route("/admin/products")
@login_required
def list_products():
    """
    Stránka s tabulkou všech produktů.
    """
    products = Product.query.all()
    return render_template("admin/products/list.html", products=products)


# ─── Přidání nového produktu přes API (POST) ─────────────────────────────────
@admin_bp.route("/admin/products/add", methods=["GET", "POST"])
@login_required
def add_product():
    """
    GET: zobrazí formulář pro přidání produktu.
    POST: odešle data a soubory na /api/products/ a vytvoří produkt.
    """
    categories = Category.query.all()

    if request.method == "POST":
        # 1) Připravíme data z formuláře
        data = {
            "name":        request.form["name"],
            "description": request.form.get("description"),
            "price":       request.form["price"],
            "category_id": request.form.get("category_id") or ""
        }

        # 2) Připravíme list pro nahrání médií
        files = []
        media_files = request.files.getlist("media")
        for mf in media_files:
            if mf and mf.filename:
                filename = secure_filename(mf.filename)
                files.append(("media", (filename, mf.stream, mf.mimetype)))

        # 3) Odešleme POST na API
        api_url = request.host_url.rstrip("/") + "/api/products/"
        response = requests.post(url=api_url, data=data, files=files)

        # 4) Vyhodnotíme odpověď
        if response.status_code == 201:
            flash("✅ Produkt byl úspěšně přidán přes API.", "success")
            return redirect(url_for("admin.list_products"))
        else:
            flash("❌ Chyba při přidávání produktu přes API.", "danger")
            return redirect(request.url)

    # GET
    return render_template("admin/products/add.html", categories=categories)


# ─── Úprava existujícího produktu přes API (PUT) ─────────────────────────────
@admin_bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    """
    GET: zobrazí formulář s předvyplněnými daty produktu.
    POST: odešle PUT na /api/products/<id> s novými daty a médii.
    """
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()

    if request.method == "POST":
        # 1) Připravíme data z formuláře
        data = {
            "name":        request.form["name"],
            "description": request.form.get("description"),
            "price":       request.form["price"],
            "category_id": request.form.get("category_id") or ""
        }

        # 2) Připravíme soubory
        files = []
        # – hlavní obrázek (jednotlivý)
        image_file = request.files.get("image")
        if image_file and image_file.filename:
            img_fn = secure_filename(image_file.filename)
            files.append(("image", (img_fn, image_file.stream, image_file.mimetype)))
        # – další média (více souborů)
        media_files = request.files.getlist("media")
        for mf in media_files:
            if mf and mf.filename:
                media_fn = secure_filename(mf.filename)
                files.append(("media", (media_fn, mf.stream, mf.mimetype)))

        # 3) Odešleme PUT na API
        api_url = request.host_url.rstrip("/") + f"/api/products/{product_id}"
        response = requests.put(url=api_url, data=data, files=files)

        # 4) Vyhodnocení
        if response.status_code == 200:
            flash("✅ Produkt byl upraven přes API.", "success")
            return redirect(url_for("admin.list_products"))
        else:
            flash("❌ Chyba při úpravě produktu přes API.", "danger")
            return redirect(request.url)

    # GET
    return render_template(
        "admin/products/edit.html",
        product=product,
        categories=categories
    )


# ─── Smazání produktu přes API (DELETE) ───────────────────────────────────────
@admin_bp.route("/admin/products/delete/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    """
    Smaže produkt (volá API DELETE) a přesměruje zpět na seznam.
    """
    api_url = request.host_url.rstrip("/") + f"/api/products/{product_id}"
    response = requests.delete(url=api_url)

    if response.status_code == 200:
        flash("🗑️ Produkt byl smazán přes API.", "info")
    else:
        flash("❌ Chyba při mazání produktu přes API.", "danger")

    return redirect(url_for("admin.list_products"))


# ─── Smazání jednoho média (obr./video) ze serveru ───────────────────────────
@admin_bp.route("/admin/media/delete/<int:media_id>", methods=["POST"])
@login_required
def delete_product_media(media_id):
    """
    Smaže soubor z disku i DB a vrátí uživatele zpět na stránku editace.
    """
    media = ProductMedia.query.get_or_404(media_id)
    product_id = media.product_id

    # 1) Smažeme fyzicky soubor z static/uploads
    file_path = os.path.join(current_app.root_path, "static/uploads", media.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # 2) Odstraníme záznam z DB
    db.session.delete(media)
    db.session.commit()

    flash("🗑️ Médium bylo smazáno.", "info")
    return redirect(url_for("admin.edit_product", product_id=product_id))
