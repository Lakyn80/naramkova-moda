# backend/auth/login_routes.py
# âś… Tento soubor obsluhuje pĹ™ihlĂˇĹˇenĂ­/odhlĂˇĹˇenĂ­
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required

# PouĹľijeme model s metodou user.check_password(...)
from backend.models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/admin")

# â”€â”€â”€ PĹ™ihlĂˇĹˇenĂ­ uĹľivatele â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    ZobrazĂ­ pĹ™ihlaĹˇovacĂ­ formulĂˇĹ™ a zpracuje pĹ™ihlĂˇĹˇenĂ­ uĹľivatele.
    """
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        # VyhledĂˇnĂ­ uĹľivatele podle username
        user = User.query.filter_by(username=username).first()

        # âś… OvÄ›Ĺ™enĂ­ hesla pĹ™es model (umĂ­ bcrypt i starĂ˝ werkzeug hash)
        if user and user.check_password(password):
            login_user(user)
            flash("âś… PĹ™ihlĂˇĹˇenĂ­ probÄ›hlo ĂşspÄ›ĹˇnÄ›.", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("âťŚ NeplatnĂ© pĹ™ihlaĹˇovacĂ­ Ăşdaje.", "danger")

    return render_template("admin/auth/login.html")

# â”€â”€â”€ OdhlĂˇĹˇenĂ­ uĹľivatele â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@auth_bp.route("/logout", methods=["GET", "POST"])
# # @login_required  # dočasně vypnuto
def logout():
    """
    OdhlĂˇsĂ­ uĹľivatele a pĹ™esmÄ›ruje zpÄ›t na login strĂˇnku.
    """
    logout_user()
    flash("đźźˇ Byli jste odhlĂˇĹˇeni.", "info")
    return redirect(url_for("auth.login"))

