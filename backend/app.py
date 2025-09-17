# backend/app.py

import os
from flask import Flask, redirect, url_for
from backend.config import Config

# ─── Rozšíření ─────────────────────────────────────────────────
from backend.extensions import db, login_manager, bcrypt, migrate, cors
from backend.extensions import init_mail

# ─── Blueprinty (produkční) ───────────────────────────────────
from backend.admin import admin_bp
from backend.auth.login_routes import auth_bp
from backend.api.routes.product_routes import api_products
from backend.api.routes.category_routes import api_categories
from backend.api.routes.media_routes import api_media
from backend.api.routes.order_routes import order_bp
from backend.client import client_bp
from backend.api.routes.payment_routes import payment_bp
from backend import models as _models  # noqa: F401
from backend.auth import login_routes  # noqa: F401
from backend.auth import password_reset_routes  # noqa: F401


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializace rozšíření
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    init_mail(app)

    # CORS – pouze produkční domény
    cors.init_app(
        app,
        resources={r"/api/*": {
            "origins": [
                "https://naramkovamoda.cz",
                "https://www.naramkovamoda.cz",
            ],
        }},
        supports_credentials=True,
        expose_headers=["Content-Disposition"],
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        always_send=True,
    )

    login_manager.login_view = "auth.login"

    # Upload dir musí existovat
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Registrace blueprintů
    app.register_blueprint(auth_bp)      # /admin/login, /admin/logout (viz auth_bp prefix)
    app.register_blueprint(admin_bp)     # /admin/... (dashboard a další)
    app.register_blueprint(api_products)
    app.register_blueprint(api_categories)
    app.register_blueprint(api_media)
    app.register_blueprint(order_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(payment_bp)

    # ✅ Redirect kořene /admin/ na dashboard (pokud nejsi přihlášen, login_manager tě pošle na login)
    @app.get("/admin/")
    def _admin_root_redirect():
        return redirect(url_for("admin.dashboard"), code=302)

    # user_loader (side-effect import)
    from backend.user_loader import load_user  # noqa: F401

    return app


# Pro gunicorn
app = create_app()

if __name__ == "__main__":
    # Lokální běh (nepoužívá se na serveru), bez debug modu
    app.run(host="127.0.0.1", port=5050)
