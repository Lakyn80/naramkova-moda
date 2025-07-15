# backend/create_admin.py

from backend.extensions import db, bcrypt
from backend.models.user import User
from flask import Flask
from backend.app import create_app

app = create_app()

@app.cli.command("create-admin")
def create_admin():
    """Vytvoří výchozího admina: username=admin, heslo=admin"""
    with app.app_context():
        if User.query.filter_by(username="admin").first():
            print("❗ Už existuje uživatel s username 'admin'.")
            return

        hashed_password = bcrypt.generate_password_hash("admin").decode("utf-8")
        admin_user = User(username="admin", password_hash=hashed_password, is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin vytvořen: admin / admin")
