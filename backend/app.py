# backend/app.py

from flask import Flask
from config import Config
from extensions import db, login_manager, bcrypt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializace rozšíření
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    login_manager.login_view = "auth.login"  # budeš-li používat Flask-Login

    # Vytvoření složky pro nahrávání souborů (např. obrázky)
    import os
    upload_path = os.path.join(app.root_path, "static", "uploads")
    os.makedirs(upload_path, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_path

    # Registrace Blueprintů (zatím zakomentováno)
    # from auth.routes import auth_bp
    # app.register_blueprint(auth_bp, url_prefix="/auth")

    # Databázové tabulky se vytvoří jen pokud běžíme přímo (ne importujeme)
    with app.app_context():
        db.create_all()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
