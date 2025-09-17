# backend/scripts/reset_admin_password_werkzeug.py
import os, sys, importlib
from werkzeug.security import generate_password_hash

SCRIPT_DIR   = os.path.abspath(os.path.dirname(__file__))
BACKEND_DIR  = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
os.environ.setdefault("DATABASE_URL", "sqlite:///instance/database.db")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def main():
    from backend.app import create_app
    from backend.extensions import db
    from backend.models.user import User  # uprav, pokud je jinde

    username = os.environ.get("ADMIN_USERNAME", "admin")
    new_pass = os.environ.get("ADMIN_PASSWORD", "admin")

    app = create_app()
    with app.app_context():
        db.create_all()
        u = db.session.query(User).filter_by(username=username).first()
        if not u:
            print(f"[ERR] User '{username}' nenalezen.")
            return
        hashed = generate_password_hash(new_pass)
        if hasattr(u, "password_hash"):
            u.password_hash = hashed
        elif hasattr(u, "password"):
            u.password = hashed
        else:
            raise RuntimeError("Model User nemá ani 'password_hash' ani 'password'.")
        # admin flagy
        for attr in ("is_admin", "is_superuser", "is_staff"):
            if hasattr(u, attr):
                setattr(u, attr, True)
        if hasattr(u, "role"):
            try:
                setattr(u, "role", "admin")
            except Exception:
                pass
        db.session.commit()
        print(f"[OK] Heslo pro '{username}' nastaveno (Werkzeug).")

if __name__ == "__main__":
    main()
