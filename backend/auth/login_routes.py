from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("✅ Přihlášení proběhlo úspěšně.", "success")
            return redirect(url_for("admin.dashboard"))  # nebo jiná stránka
        else:
            flash("❌ Neplatné přihlašovací údaje.", "danger")

    return render_template("admin/auth/login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("🟡 Byli jste odhlášeni.", "info")
    return redirect(url_for("auth.login"))
