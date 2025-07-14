import os
from flask import Flask
from config import Config
from extensions import db, login_manager, bcrypt, migrate, cors
from admin import admin_bp
from auth.login_routes import auth_bp
from api.routes.product_routes import api_products
from api.routes.category_routes import api_categories
from api.routes.media_routes import api_media


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # ─── Inicializace rozšíření ───────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})  # <-- CORS povoleno pro React

    login_manager.login_view = "auth.login"

    # ─── Vytvoření složky pro upload obrázků ──────────────────────────────
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ─── Registrace blueprintů ────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_products)
    app.register_blueprint(api_categories)
    app.register_blueprint(api_media)

    # ─── Import user_loader kvůli Flask-Login ─────────────────────────────
    from user_loader import load_user  # noqa: F401

    return app


# ─── Spuštění aplikace ─────────────────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
