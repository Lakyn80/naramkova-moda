import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask
from backend.config import Config

# ─── Načtení rozšíření ──────────────────────────────────────────
from backend.extensions import db, login_manager, bcrypt, migrate, cors, mail

# ─── Načtení jednotlivých blueprintů ────────────────────────────
from backend.admin import admin_bp
from backend.auth.login_routes import auth_bp
from backend.api.routes.product_routes import api_products
from backend.api.routes.category_routes import api_categories
from backend.api.routes.media_routes import api_media
from backend.client import client_bp
from backend.api.routes.payment_routes import payment_bp
from backend.debug_routes import debug_bp
from backend import models as _models  # noqa: F401

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)

    cors.init_app(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",
                "http://localhost:5173",
                "https://lakyn80.github.io"
            ],
            "supports_credentials": True
        }
    })

    login_manager.login_view = "auth.login"
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_products)
    app.register_blueprint(api_categories)
    app.register_blueprint(api_media)
    app.register_blueprint(client_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(debug_bp)

    from backend.user_loader import load_user  # noqa: F401

    return app

# ✅ GUNICORN potřebuje tento řádek
app = create_app()

# ✅ Toto je jen pro lokální vývoj
if __name__ == "__main__":
    app.run(debug=True)
