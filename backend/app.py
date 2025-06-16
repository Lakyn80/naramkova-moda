import os
from flask import Flask
from config import Config
from extensions import db, login_manager, bcrypt, migrate
from admin import admin_bp
from auth.login_routes import auth_bp

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # ─── Inicializace rozšíření ───────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    login_manager.login_view = "auth.login"

    # ─── Vytvoření složky pro upload obrázků ──────────────────────────────
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ─── Registrace blueprintů ────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # ─── Import user_loader kvůli Flask-Login ─────────────────────────────
    from user_loader import load_user  # noqa: F401

    return app

# ─── Spuštění aplikace ─────────────────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
