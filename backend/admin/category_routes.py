from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from . import admin_bp
from backend.extensions import db
# ZMÄšNA: Importuj pĹ™Ă­mo z hlavnĂ­ch modelĹŻ, ne z admin.models
from backend.models import Category

@admin_bp.route("/categories")
# # # # @login_required  # dočasně vypnuto (dočasně vypnuto)
def list_categories():
    search = (request.args.get("q") or "").strip()
    group_filter = (request.args.get("group") or "").strip()
    page = max(int(request.args.get("page", 1) or 1), 1)

    query = Category.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Category.name.ilike(like)) | (Category.description.ilike(like))
        )
    if group_filter:
        query = query.filter(Category.group == group_filter)

    pagination = query.order_by(Category.name.asc()).paginate(
        page=page, per_page=50, error_out=False
    )
    categories = pagination.items

    group_rows = (
        db.session.query(Category.group)
        .filter(Category.group.isnot(None))
        .distinct()
        .order_by(Category.group.asc())
        .all()
    )
    groups = [g[0] for g in group_rows if g[0]]

    return render_template(
        "admin/categories/list.html",
        categories=categories,
        pagination=pagination,
        search=search,
        group_filter=group_filter,
        groups=groups,
    )

@admin_bp.route("/categories/add", methods=["GET", "POST"])
# # # # @login_required  # dočasně vypnuto (dočasně vypnuto)
def add_category():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()

        # formulĂˇĹ™ mĹŻĹľe poslat name="category" (novÄ›) nebo starĂ© name="group"
        group_val = (request.form.get("category") or request.form.get("group") or "").strip()

        if not name:
            flash("Název je povinný.", "danger")
            return redirect(url_for("admin.add_category"))

        db.session.add(Category(name=name, description=(description or None), group=(group_val or None)))
        db.session.commit()
        flash("✔ Kategorie byla přidána.", "success")
        return redirect(url_for("admin.list_categories"))

    return render_template("admin/categories/add.html")

@admin_bp.route("/categories/edit/<int:category_id>", methods=["GET", "POST"])
# # # # @login_required  # dočasně vypnuto (dočasně vypnuto)
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        group_val = (request.form.get("category") or request.form.get("group") or "").strip()

        if not name:
            flash("Název je povinný.", "danger")
            return redirect(url_for("admin.edit_category", category_id=category_id))

        category.name = name
        category.description = description or None
        category.group = group_val or None
        db.session.commit()
        flash("✔ Kategorie byla upravena.", "success")
        return redirect(url_for("admin.list_categories"))

    return render_template("admin/categories/edit.html", category=category)

@admin_bp.route("/categories/delete/<int:category_id>", methods=["POST"])
# # # # @login_required  # dočasně vypnuto (dočasně vypnuto)
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash("🗑️ Kategorie byla smazána.", "info")
    return redirect(url_for("admin.list_categories"))




