import os
from flask import Flask
from config import Config
from extensions import db, login_manager, bcrypt
from admin import admin_bp
from auth.login_routes import auth_bp

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # ─── Inicializace rozšíření ───────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    login_manager.login_view = "auth.login"

    # ─── Cesty ────────────────────────────────────────────────────────────
    os.makedirs(os.path.join(app.root_path, "static", "uploads"), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "instance"), exist_ok=True)

    # ─── Blueprinty ───────────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # ─── Databáze ─────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    from user_loader import load_user  # noqa: F401

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
