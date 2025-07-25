# ✅ Tento soubor obsluhuje přihlášení/odhlášení
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash

# ✅ Opravený import modelu User
from backend.models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# ─── Přihlášení uživatele ─────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Zobrazí přihlašovací formulář a zpracuje přihlášení uživatele.
    """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Vyhledání uživatele podle username
        user = User.query.filter_by(username=username).first()

        # Ověření hesla
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("✅ Přihlášení proběhlo úspěšně.", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("❌ Neplatné přihlašovací údaje.", "danger")

    return render_template("admin/auth/login.html")

# ─── Odhlášení uživatele ─────────────────────────────────────────────
@auth_bp.route("/logout")
@login_required
def logout():
    """
    Odhlásí uživatele a přesměruje zpět na login stránku.
    """
    logout_user()
    flash("🟡 Byli jste odhlášeni.", "info")
    return redirect(url_for("auth.login"))
