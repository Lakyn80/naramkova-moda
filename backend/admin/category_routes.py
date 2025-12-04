from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from . import admin_bp
from backend.extensions import db
# ZMÄšNA: Importuj pĹ™Ă­mo z hlavnĂ­ch modelĹŻ, ne z admin.models
from backend.models import Category

@admin_bp.route("/categories")
# # # # @login_required  # dočasně vypnuto (dočasně vypnuto)
def list_categories():
    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template("admin/categories/list.html", categories=categories)

@admin_bp.route("/categories/add", methods=["GET", "POST"])
# # # # @login_required  # dočasně vypnuto (dočasně vypnuto)
def add_category():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()

        # formulĂˇĹ™ mĹŻĹľe poslat name="category" (novÄ›) nebo starĂ© name="group"
        group_val = (request.form.get("category") or request.form.get("group") or "").strip()

        if not name:
            flash("NĂˇzev je povinnĂ˝.", "danger")
            return redirect(url_for("admin.add_category"))

        db.session.add(Category(name=name, description=(description or None), group=(group_val or None)))
        db.session.commit()
        flash("âś… Kategorie byla pĹ™idĂˇna.", "success")
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
            flash("NĂˇzev je povinnĂ˝.", "danger")
            return redirect(url_for("admin.edit_category", category_id=category_id))

        category.name = name
        category.description = description or None
        category.group = group_val or None
        db.session.commit()
        flash("âś… Kategorie byla upravena.", "success")
        return redirect(url_for("admin.list_categories"))

    return render_template("admin/categories/edit.html", category=category)

@admin_bp.route("/categories/delete/<int:category_id>", methods=["POST"])
# # # # @login_required  # dočasně vypnuto (dočasně vypnuto)
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash("đź—‘ď¸Ź Kategorie byla smazĂˇna.", "info")
    return redirect(url_for("admin.list_categories"))




