import os
import requests
from flask import render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_required, current_user

from backend.admin import admin_bp
from backend.extensions import db
from backend.admin.models import Product, Category, ProductMedia
from werkzeug.utils import secure_filename


def _file_tuple(fs):
    """Vrátí (filename, fileobj, mimetype). ŽÁDNÉ placeholdery ani zásahy do URL (HARD RULES)."""
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


# -----------------------------------------------------------------------------
# LIST PRODUKTŮ
# -----------------------------------------------------------------------------
@admin_bp.route("/products", endpoint="products")
@login_required
def products_list():
    """
    Filtry se perzistují do session['admin_products_filters'].
    - ?reset=1 → vyčistí uložené filtry.
    - Když nejsou query parametry, ale session má filtry → použijeme session.
    - Stránkování nese aktivní filtry dál.
    """
    # reset filtrů?
    if request.args.get("reset") == "1":
        session.pop("admin_products_filters", None)
        return redirect(url_for("admin.products"))

    # načti query (pokud nějaké jsou)
    raw_args = request.args.to_dict(flat=True)

    # určím, zda jsou v URL skutečné filtry (kromě page)
    url_has_filters = any(
        k in raw_args and raw_args[k] not in ("", None)
        for k in ["q", "category_id", "has_image", "has_media", "price_min", "price_max", "stock_min", "stock_max", "sort"]
    )

    # když nejsou query filtry a máme uložené v session → použij je
    saved = session.get("admin_products_filters") or {}
    if not url_has_filters and saved:
        # zachovej page z URL (pokud je), ale aplikuj uložené filtry
        merged = {**saved}
        if "page" in raw_args:
            merged["page"] = raw_args["page"]
        return redirect(url_for("admin.products", **merged))

    # ---- bezpečné parsování hodnot z request.args ----
    def _to_int(val):
        try:
            return int(val) if val not in (None, "",) else None
        except Exception:
            return None

    def _to_float(val):
        try:
            return float(val) if val not in (None, "",) else None
        except Exception:
            return None

    q = (request.args.get("q") or "").strip()
    category_id = _to_int(request.args.get("category_id"))
    has_image = request.args.get("has_image")  # "1" → jen s obrázkem
    has_media = request.args.get("has_media")  # "1" → jen s médii
    price_min = _to_float(request.args.get("price_min"))
    price_max = _to_float(request.args.get("price_max"))
    stock_min = _to_int(request.args.get("stock_min"))
    stock_max = _to_int(request.args.get("stock_max"))
    sort = request.args.get("sort") or "id_desc"

    # ---- Základní dotaz ----
    query = Product.query

    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if has_image == "1":
        query = query.filter(Product.image.isnot(None), Product.image != "")
    if has_media == "1":
        query = query.filter(Product.media.any())

    if price_min is not None:
        query = query.filter(Product.price_czk >= price_min)
    if price_max is not None:
        query = query.filter(Product.price_czk <= price_max)

    if stock_min is not None:
        query = query.filter(Product.stock >= stock_min)
    if stock_max is not None:
        query = query.filter(Product.stock <= stock_max)

    # ---- ŘAZENÍ ----
    created_col = getattr(Product, "created_at", None)
    if sort == "id_asc":
        query = query.order_by(Product.id.asc())
    elif sort == "id_desc":
        query = query.order_by(Product.id.desc())
    elif sort == "name_asc":
        query = query.order_by(Product.name.asc())
    elif sort == "name_desc":
        query = query.order_by(Product.name.desc())
    elif sort == "price_asc":
        query = query.order_by(Product.price_czk.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price_czk.desc())
    elif sort == "date_asc":
        query = query.order_by((created_col.asc() if created_col is not None else Product.id.asc()))
    elif sort == "date_desc":
        query = query.order_by((created_col.desc() if created_col is not None else Product.id.desc()))
    else:
        query = query.order_by(Product.id.desc())

    # ---- Stránkování ----
    page = _to_int(request.args.get("page")) or 1
    per_page = 30
    total = query.count()
    max_pages = (total + per_page - 1) // per_page if total else 1
    if page < 1:
        page = 1
    if page > max_pages:
        page = max_pages

    products = query.offset((page - 1) * per_page).limit(per_page).all()
    categories = Category.query.order_by(Category.group.asc(), Category.name.asc()).all()

    # ---- Ulož/aktualizuj filtry do session (bez page) ----
    session["admin_products_filters"] = {
        "q": q or None,
        "category_id": category_id,
        "has_image": "1" if has_image == "1" else None,
        "has_media": "1" if has_media == "1" else None,
        "price_min": str(price_min) if price_min is not None else None,
        "price_max": str(price_max) if price_max is not None else None,
        "stock_min": str(stock_min) if stock_min is not None else None,
        "stock_max": str(stock_max) if stock_max is not None else None,
        "sort": sort or "id_desc",
    }

    return render_template(
        "admin/products/list.html",
        products=products,
        categories=categories,
        # předvyplnění polí
        q=q,
        selected_category_id=category_id,
        selected_has_image=(has_image == "1"),
        selected_has_media=(has_media == "1"),
        price_min=("" if price_min is None else price_min),
        price_max=("" if price_max is None else price_max),
        stock_min=("" if stock_min is None else stock_min),
        stock_max=("" if stock_max is None else stock_max),
        selected_sort=sort,
        # pagination info
        page=page,
        per_page=per_page,
        total=total,
        max_pages=max_pages,
        has_prev=(page > 1),
        has_next=(page < max_pages),
    )


# -----------------------------------------------------------------------------
# PŘIDÁNÍ PRODUKTU (proxy přes API)
# -----------------------------------------------------------------------------
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
            "stock": request.form.get("stock", "1"),
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
            return redirect(url_for("admin.products"))
        else:
            flash("❌ Chyba při přidávání produktu přes API.", "danger")
            return redirect(request.url)

    return render_template("admin/products/add.html", categories=categories, category_labels=category_labels)


# -----------------------------------------------------------------------------
# ÚPRAVA PRODUKTU (proxy přes API)
# -----------------------------------------------------------------------------
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
            "stock": request.form.get("stock", ""),
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
            return redirect(url_for("admin.products"))
        else:
            flash("❌ Chyba při úpravě produktu přes API.", "danger")
            return redirect(request.url)

    return render_template(
        "admin/products/edit.html",
        product=product,
        categories=categories,
        category_labels=category_labels,
    )


# -----------------------------------------------------------------------------
# SMAZÁNÍ PRODUKTU (proxy přes API)
# -----------------------------------------------------------------------------
@admin_bp.route("/products/delete/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id: int):
    api_url = request.host_url.rstrip("/") + f"/api/products/{product_id}"
    try:
        response = requests.delete(url=api_url)
    except Exception as e:
        flash(f"❌ Chyba volání API: {e}", "danger")
        return redirect(url_for("admin.products"))

    if response.status_code == 200:
        flash("🗑️ Produkt byl smazán přes API.", "info")
    else:
        flash("❌ Chyba při mazání produktu přes API.", "danger")

    return redirect(url_for("admin.products"))


# -----------------------------------------------------------------------------
# SMAZÁNÍ JEDNOHO MÉDIA
# -----------------------------------------------------------------------------
@admin_bp.route(
    "/products/media/delete/<int:media_id>",
    methods=["POST"],
    endpoint="delete_product_media",
)
@login_required
def delete_product_media(media_id: int):
    media = ProductMedia.query.get(media_id)
    if not media:
        flash("❌ Médium neexistuje.", "danger")
        return redirect(url_for("admin.products"))

    product_id = media.product_id
    filename = media.filename
    file_path = os.path.join(current_app.root_path, "static", "uploads", filename)

    # nezasahovat, pokud je to main image produktu
    is_same_as_main = False
    product = Product.query.get(media.product_id)
    if product and product.image and product.image == filename:
        is_same_as_main = True

    # pokud soubor sdílí více záznamů, nemaž fyzicky
    shared_count = ProductMedia.query.filter(ProductMedia.filename == filename).count()

    if not is_same_as_main and shared_count <= 1:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

    db.session.delete(media)
    db.session.commit()

    flash("🗑️ Fotka/medium bylo smazáno.", "info")
    return redirect(url_for("admin.edit_product", product_id=product_id))
