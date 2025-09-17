# backend/scripts/seed_dev_minimal.py
import os, sys, importlib
from datetime import datetime, UTC

# Cesty
SCRIPT_DIR   = os.path.abspath(os.path.dirname(__file__))   # .../backend/scripts
BACKEND_DIR  = os.path.dirname(SCRIPT_DIR)                  # .../backend
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)                 # <root>

# ENV
os.environ.setdefault("DATABASE_URL", "sqlite:///instance/database.db")

# Importy přes balíček backend.*
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def get_app_db_models():
    backend_app = importlib.import_module("backend.app")
    create_app = getattr(backend_app, "create_app", None)
    if callable(create_app):
        app = create_app()
    else:
        app = getattr(backend_app, "app")
    ext = importlib.import_module("backend.extensions")
    db = ext.db
    models = importlib.import_module("backend.admin.models")
    # Fallback: kdyby create_app nevolalo db.init_app(app)
    if not getattr(app, "extensions", None) or "sqlalchemy" not in app.extensions:
        db.init_app(app)
    return app, db, models

def main():
    app, db, models = get_app_db_models()
    Order   = models.Order
    Payment = models.Payment

    now = datetime.now(UTC)
    vs  = "00000001"

    with app.app_context():
        # VYTVOŘ OBJEDNÁVKU – doplň povinné údaje
        o = Order(
            vs=vs,
            status="awaiting_payment",
            total_czk=199.0,
            customer_name="Test User",
            customer_email="test@example.com",
            customer_address="Test Street 1, 11000 Praha",
            note="seed order",
            created_at=now,
        )
        db.session.add(o)
        db.session.flush()  # pro jistotu mít o.id

        # VYTVOŘ PLATBU
        p = Payment(
            vs=vs,
            status="pending",
            amount_czk=199.0,
            reference="seed",
            received_at=now,
        )
        db.session.add(p)

        db.session.commit()
        print(f"[OK] Seeded Order #{o.id} (vs={vs}) and Payment #{p.id}")

if __name__ == "__main__":
    main()
