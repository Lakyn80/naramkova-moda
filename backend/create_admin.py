# backend/create_admin.py
import os
import click
from flask import Flask
from werkzeug.security import generate_password_hash
from backend.app import create_app
from backend.extensions import db

app: Flask = create_app()

@app.cli.command("create-admin")
@click.option("--username", default=lambda: os.environ.get("ADMIN_USERNAME", "admin"),
              show_default=True, help="Admin username")
@click.option("--email", default=lambda: os.environ.get("ADMIN_EMAIL", "admin@example.com"),
              show_default=True, help="Admin e-mail (pokud model má sloupec email)")
@click.option("--password", default=lambda: os.environ.get("ADMIN_PASSWORD"),
              help="Heslo (když není zadáno, zeptám se interaktivně)")
@click.option("--force", is_flag=True, default=False,
              help="Pokud už existuje, resetnu mu heslo a roli")
def create_admin(username: str, email: str, password: str | None, force: bool):
    """Vytvoří / resetne admin účet. Hashuje přes Werkzeug (pbkdf2:sha256)."""
    # Import až po vytvoření app (aby byly modely správně zaregistrované)
    from backend.models.user import User  # uprav, pokud máš jinde

    with app.app_context():
        db.create_all()  # pro případ prázdné DB

        if not password:
            password = click.prompt("Zadej heslo", hide_input=True, confirmation_prompt=True)

        # najdi existujícího
        q = db.session.query(User)
        u = q.filter_by(username=username).first()
        if u and not force:
            click.echo(f"❗ Uživatel '{username}' už existuje. Použij --force pro reset hesla.")
            return

        if not u:
            u = User(username=username)
            if hasattr(u, "email"):
                setattr(u, "email", email)
            db.session.add(u)

        # admin flagy
        for attr in ("is_admin", "is_superuser", "is_staff"):
            if hasattr(u, attr):
                setattr(u, attr, True)
        if hasattr(u, "role"):
            try:
                setattr(u, "role", "admin")
            except Exception:
                pass

        # nastav hash přes Werkzeug (aby seděl s loginem)
        hashed = generate_password_hash(password)
        if hasattr(u, "password_hash"):
            u.password_hash = hashed
        elif hasattr(u, "password"):
            u.password = hashed
        else:
            raise RuntimeError("Model User nemá ani 'password_hash' ani 'password'.")

        db.session.commit()
        click.echo(f"✅ Admin připraven: {username}")
