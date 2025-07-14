# ✅ Import základních Flask věcí
from flask import render_template, request, redirect, url_for, flash

# ✅ Login required pro přístup do admin sekce
from flask_login import login_required

# ✅ Blueprint admin_bp pro routy v admin části
from backend.admin import admin_bp

# ✅ Správný import db z backend.extensions
from backend.extensions import db

# ✅ Import Category modelu
from backend.admin.models import Category


# ─────────────────────────────────────────────────────────────────────────────
# 🔍 Výpis všech kategorií
@admin_bp.route("/categories")
@login_required
def list_categories():
    categories = Category.query.all()  # Načteme všechny z databáze
    return render_template("admin/categories/list.html", categories=categories)


# ─────────────────────────────────────────────────────────────────────────────
# ➕ Přidání nové kategorie
@admin_bp.route("/categories/add", methods=["GET", "POST"])
@login_required
def add_category():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form.get("description")

        # ✅ Vytvoříme novou instanci Category
        new_category = Category(name=name, description=description)
        db.session.add(new_category)
        db.session.commit()

        flash("✅ Kategorie byla přidána.", "success")
        return redirect(url_for("admin.list_categories"))

    return render_template("admin/categories/add.html")


# ─────────────────────────────────────────────────────────────────────────────
# 📝 Úprava kategorie
@admin_bp.route("/categories/edit/<int:category_id>", methods=["GET", "POST"])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)

    if request.method == "POST":
        category.name = request.form["name"]
        category.description = request.form.get("description")
        db.session.commit()

        flash("✅ Kategorie byla upravena.", "success")
        return redirect(url_for("admin.list_categories"))

    return render_template("admin/categories/edit.html", category=category)


# ─────────────────────────────────────────────────────────────────────────────
# 🗑️ Smazání kategorie
@admin_bp.route("/categories/delete/<int:category_id>", methods=["POST"])
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()

    flash("🗑️ Kategorie byla smazána.", "info")
    return redirect(url_for("admin.list_categories"))
