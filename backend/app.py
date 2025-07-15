# 📁 backend/app.py
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
from backend.admin.sold_routes import sold_bp


def create_app() -> Flask:
    """
    Tovární funkce pro vytvoření Flask aplikace.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # ─── Inicializace rozšíření ─────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    cors.init_app(app)

    # Povolení CORS pro React frontend na localhostu
    cors.init_app(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

    # Přesměrování na login, pokud není přihlášený uživatel
    login_manager.login_view = "auth.login"

    # ─── Zajištění složky pro uploady ───────────────────────────
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ─── Registrace všech blueprintů ─────────────────────────────
    app.register_blueprint(auth_bp)         # Přihlášení (admin)
    app.register_blueprint(admin_bp)        # Admin rozhraní
    app.register_blueprint(api_products)    # API pro produkty
    app.register_blueprint(api_categories)  # API pro kategorie (frontend)
    app.register_blueprint(api_media)       # API pro obrázky/videa
    app.register_blueprint(client_bp)       # Klientské API pro objednávky
    app.register_blueprint(sold_bp)         # Správa prodaných produktů

    # ─── User loader pro Flask-Login ─────────────────────────────
    from backend.user_loader import load_user  # noqa: F401

    return app


# ─── Spuštění aplikace ───────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
