import os
from flask import render_template, request, redirect, url_for, flash, current_app
from math import ceil
from flask_login import login_required
from . import admin_bp
from backend.extensions import db
from backend.models import Product, Category, ProductMedia, ProductVariant, ProductVariantMedia, SoldProduct, Payment
from backend.api.routes.product_routes import (
    _parse_variants_from_request,
    _process_and_save_image,
    _detect_media_type,
    _save_raw,
)
from backend.api.routes.product_routes import _process_and_save_image


@admin_bp.route("/")
# # # # @login_required  # docasne vypnuto
def dashboard():
    product_count = Product.query.count()
    category_count = Category.query.count()
    sold_count = SoldProduct.query.count()
    payment_count = Payment.query.count()
    return render_template(
        "admin/dashboard.html",
        product_count=product_count,
        category_count=category_count,
        sold_count=sold_count,
        payment_count=payment_count,
    )


@admin_bp.route("/products", endpoint="products")
# # # # @login_required  # docasne vypnuto
def product_list():
    categories = Category.query.order_by(Category.name.asc()).all()

    q = (request.args.get("q") or "").strip()
    category_id = request.args.get("category_id", type=int)
    price_min = request.args.get("price_min", type=float)
    price_max = request.args.get("price_max", type=float)
    stock_min = request.args.get("stock_min", type=int)
    stock_max = request.args.get("stock_max", type=int)
    has_image = request.args.get("has_image") is not None
    has_media = request.args.get("has_media") is not None
    sort = request.args.get("sort") or "id_desc"

    query = Product.query
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if price_min is not None:
        query = query.filter(Product.price_czk >= price_min)
    if price_max is not None:
        query = query.filter(Product.price_czk <= price_max)
    if stock_min is not None:
        query = query.filter(Product.stock >= stock_min)
    if stock_max is not None:
        query = query.filter(Product.stock <= stock_max)
    if has_image:
        query = query.filter(Product.image.isnot(None))
    if has_media:
        query = query.filter(Product.media.any())

    sort_map = {
        "id_desc": Product.id.desc(),
        "id_asc": Product.id.asc(),
        "date_desc": Product.created_at.desc(),
        "date_asc": Product.created_at.asc(),
        "name_asc": Product.name.asc(),
        "name_desc": Product.name.desc(),
        "price_asc": Product.price_czk.asc(),
        "price_desc": Product.price_czk.desc(),
    }
    query = query.order_by(sort_map.get(sort, Product.id.desc()))

    # stránkování (50 na stránku)
    per_page = 50
    page = max(int(request.args.get("page") or 1), 1)
    total = query.count()
    max_pages = max(1, ceil(total / per_page))
    if page > max_pages:
        page = max_pages
    products = query.limit(per_page).offset((page - 1) * per_page).all()
    has_prev = page > 1
    has_next = page < max_pages

    return render_template(
        "admin/products/list.html",
        products=products,
        categories=categories,
        q=q,
        selected_category_id=category_id,
        selected_has_image=has_image,
        selected_has_media=has_media,
        price_min=price_min,
        price_max=price_max,
        stock_min=stock_min,
        stock_max=stock_max,
        selected_sort=sort,
        page=page,
        max_pages=max_pages,
        has_prev=has_prev,
        has_next=has_next,
    )


@admin_bp.route("/products/add", methods=["GET", "POST"], endpoint="add_product")
# # # # @login_required  # docasne vypnuto
def product_add():
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price") or request.form.get("price_czk")
        description = request.form.get("description")
        stock_val = request.form.get("stock")
        category_id = request.form.get("category_id")

        product = Product()
        product.name = name
        product.price_czk = price
        product.description = description
        try:
            product.stock = int(stock_val)
        except Exception:
            pass
        product.category_id = category_id

        db.session.add(product)
        db.session.flush()

        image_file = request.files.get("image")
        if image_file and image_file.filename:
            product.image = _process_and_save_image(image_file)

        for mf in request.files.getlist("media"):
            if not mf or not mf.filename:
                continue
            media_type = _detect_media_type(mf.filename, mf.mimetype)
            if media_type == "image":
                saved_name = _process_and_save_image(mf)
            else:
                saved_name = _save_raw(mf)
            db.session.add(ProductMedia(product_id=product.id, filename=saved_name, media_type=media_type))

        variants_payload, _ = _parse_variants_from_request()
        for variant in variants_payload:
            img_name = variant.get("image") or variant.get("existing_image") or None
            if variant.get("image_file"):
                img_name = _process_and_save_image(variant["image_file"])

            if not (variant.get("variant_name") or variant.get("wrist_size") or img_name):
                continue

            v_obj = ProductVariant(
                product_id=product.id,
                variant_name=variant.get("variant_name"),
                wrist_size=variant.get("wrist_size"),
                description=variant.get("description"),
                price_czk=variant.get("price_czk"),
                stock=variant.get("stock") or 0,
                image=img_name,
            )
            db.session.add(v_obj)

            for ef in variant.get("extra_files") or []:
                saved = _process_and_save_image(ef)
                db.session.add(ProductVariantMedia(variant=v_obj, filename=saved))
            for keep in variant.get("existing_extra") or []:
                db.session.add(ProductVariantMedia(variant=v_obj, filename=keep))

        db.session.commit()

        flash("Produkt byl pridan.", "success")
        return redirect(url_for("admin.products"))

    categories = Category.query.all()
    return render_template("admin/products/add.html", categories=categories)


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"], endpoint="edit_product")
# # # # @login_required  # docasne vypnuto
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        product.name = request.form.get("name")
        price_val = request.form.get("price") or request.form.get("price_czk")
        description = request.form.get("description")
        stock_val = request.form.get("stock")
        product.price_czk = price_val
        product.description = description
        try:
            product.stock = int(stock_val)
        except Exception:
            pass
        product.category_id = request.form.get("category_id")

        if request.form.get("delete_image") == "1":
          if product.image:
            try:
              os.remove(os.path.join(current_app.root_path, "static", "uploads", product.image))
            except Exception:
              pass
          product.image = None

        image_file = request.files.get("image")
        if image_file and image_file.filename:
            old_image = product.image
            product.image = _process_and_save_image(image_file)
            if old_image and old_image != product.image:
                try:
                    os.remove(os.path.join(current_app.root_path, "static", "uploads", old_image))
                except Exception:
                    pass

        for mf in request.files.getlist("media"):
            if not mf or not mf.filename:
                continue
            media_type = _detect_media_type(mf.filename, mf.mimetype)
            if media_type == "image":
                saved_name = _process_and_save_image(mf)
            else:
                saved_name = _save_raw(mf)
            db.session.add(ProductMedia(product_id=product.id, filename=saved_name, media_type=media_type))

        variants_payload, variants_explicit = _parse_variants_from_request()

        if variants_explicit:
            old_variants = list(product.variants or [])
            existing_files: set[str] = set()
            for ov in old_variants:
                if ov.image:
                    existing_files.add(ov.image)
                for mv in list(ov.media or []):
                    if mv.filename:
                        existing_files.add(mv.filename)

            product.variants.clear()
            new_files: set[str] = set()

            for variant in variants_payload:
                img_name = variant.get("image") or variant.get("existing_image") or None
                if variant.get("image_file"):
                    img_name = _process_and_save_image(variant["image_file"])

                if not (variant.get("variant_name") or variant.get("wrist_size") or img_name):
                    continue

                if img_name:
                    new_files.add(img_name)

                extra_existing = variant.get("existing_extra") or []
                extra_saved: list[str] = []
                for ef in variant.get("extra_files") or []:
                    extra_saved.append(_process_and_save_image(ef))

                new_files.update(extra_existing)
                new_files.update(extra_saved)

                v_obj = ProductVariant(
                    product_id=product.id,
                    variant_name=variant.get("variant_name"),
                    wrist_size=variant.get("wrist_size"),
                    description=variant.get("description"),
                    price_czk=variant.get("price_czk"),
                    stock=variant.get("stock") or 0,
                    image=img_name,
                )
                db.session.add(v_obj)
                for fn in extra_existing:
                    db.session.add(ProductVariantMedia(variant=v_obj, filename=fn))
                for fn in extra_saved:
                    db.session.add(ProductVariantMedia(variant=v_obj, filename=fn))

            for fname in existing_files - new_files:
                try:
                    os.remove(os.path.join(current_app.root_path, "static", "uploads", fname))
                except Exception:
                    pass

        db.session.commit()

        flash("Produkt upraven.", "success")
        return redirect(url_for("admin.edit_product", product_id=product.id))

    categories = Category.query.all()
    return render_template("admin/products/edit.html", product=product, categories=categories)


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"], endpoint="delete_product")
# # # # @login_required  # docasne vypnuto
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)

    db.session.delete(product)
    db.session.commit()

    flash("Produkt odstraněn.", "warning")
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/media/<int:media_id>/delete", methods=["POST"], endpoint="delete_product_media")
def delete_product_media(media_id):
    media = ProductMedia.query.get_or_404(media_id)

    # Remove file from uploads if it exists
    try:
        file_path = os.path.join(current_app.root_path, "static", "uploads", media.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        current_app.logger.exception("Failed to remove media file for id=%s", media_id)

    db.session.delete(media)
    db.session.commit()
    flash("Medium bylo smazano.", "info")
    return redirect(request.referrer or url_for("admin.products"))
