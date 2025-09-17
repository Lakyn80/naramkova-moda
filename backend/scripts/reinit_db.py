# backend/scripts/reinit_db.py
import os, sys, shutil, datetime, importlib

# ── Cesty ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = os.path.abspath(os.path.dirname(__file__))   # .../backend/scripts
BACKEND_DIR  = os.path.dirname(SCRIPT_DIR)                  # .../backend
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)                 # repo root
INSTANCE_DIR = os.path.join(BACKEND_DIR, "instance")
DB_FILE      = os.path.join(INSTANCE_DIR, "database.db")

# ── ENV: SQLite v instance/ ─────────────────────────────────────────────────
os.makedirs(INSTANCE_DIR, exist_ok=True)
os.environ.setdefault("DATABASE_URL", "sqlite:///instance/database.db")

# Importuj přes balíček "backend.*", ne přes file-path (ať nevzniknou 2 moduly)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def get_app_and_db():
    backend_app = importlib.import_module("backend.app")
    create_app = getattr(backend_app, "create_app", None)
    if callable(create_app):
        app = create_app()
    else:
        app = getattr(backend_app, "app", None)
        if app is None:
            raise RuntimeError("V backend.app chybí create_app() i app.")
    ext = importlib.import_module("backend.extensions")
    db  = getattr(ext, "db")
    # Fallback: kdyby create_app nevolalo db.init_app(app)
    if not getattr(app, "extensions", None) or "sqlalchemy" not in app.extensions:
        db.init_app(app)
    return app, db

def main():
    # 1) backup + smazání staré DB (pokud existuje)
    if os.path.exists(DB_FILE):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = os.path.join(INSTANCE_DIR, f"database_backup_{ts}.db")
        shutil.copy2(DB_FILE, backup)
        os.remove(DB_FILE)
        print(f"[OK] Old DB removed. Backup -> {backup}")
    else:
        print("[OK] No existing DB; starting fresh.")

    # 2) app + db
    app, db = get_app_and_db()

    # 3) vytvoř tabulky
    with app.app_context():
        # DŮLEŽITÉ: Načti modely, aby se zaregistrovaly do SQLAlchemy
        try:
            importlib.import_module("backend.admin.models")
        except ModuleNotFoundError:
            pass
        try:
            importlib.import_module("backend.models")
        except ModuleNotFoundError:
            pass

        db.create_all()

        # SQLAlchemy 2.0 styl listování tabulek
        from sqlalchemy import text
        try:
            with db.engine.connect() as conn:
                rows = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
                )).fetchall()
            print("[INFO] Tables created:", ", ".join(r[0] for r in rows))
        except Exception as e:
            print("[WARN] Could not list tables:", e)

    print("[DONE] Fresh database created at:", DB_FILE)

if __name__ == "__main__":
    main()
