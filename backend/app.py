import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask
from backend.config import Config

# 🧩 Rozšíření
from backend.extensions import db, login_manager, bcrypt, migrate, cors, mail

# 🧩 Blueprints
from backend.admin import admin_bp
from backend.auth.login_routes import auth_bp
from backend.api.routes.product_routes import api_products
from backend.api.routes.category_routes import api_categories
from backend.api.routes.media_routes import api_media
from backend.client import client_bp
from backend.admin.sold_routes import sold_bp
from backend.api.routes.payment_routes import payment_bp

def create_app() -> Flask:
    instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance")
    app = Flask(__name__, instance_path=instance_path)
    app.config.from_object(Config)

    # ✅ Rozšíření
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)

    # ✅ CORS pro všechny relevantní frontend původy
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",                       # Lokální vývoj
                "https://lakyn80.github.io",                  # GitHub Pages
                "https://naramkova-moda.web.app",             # (budoucí Firebase hosting)
            ]
        }
    })

    login_manager.login_view = "auth.login"
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ✅ Registrace blueprintů
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_products)
    app.register_blueprint(api_categories)
    app.register_blueprint(api_media)
    app.register_blueprint(client_bp)
    app.register_blueprint(sold_bp)
    app.register_blueprint(payment_bp)

    from backend.user_loader import load_user  # noqa: F401

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
