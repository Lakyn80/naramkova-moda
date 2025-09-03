# backend/scripts/wipe_non_category.py
from __future__ import annotations
import os, sys, shutil
from datetime import datetime
from importlib.machinery import SourceFileLoader

# ---- Najdi backend/app.py bez ohledu na to, odkud se skript spouští
THIS_DIR = os.path.abspath(os.path.dirname(__file__))              # .../backend/scripts
BACKEND_DIR = os.path.abspath(os.path.join(THIS_DIR, ".."))        # .../backend
APP_PATH = os.path.join(BACKEND_DIR, "app.py")                     # .../backend/app.py

if not os.path.isfile(APP_PATH):
    raise SystemExit(f"❌ Nenalezen backend/app.py na {APP_PATH}")

# Načti backend/app.py jako modul (bez importu balíčku 'backend')
app_mod = SourceFileLoader("backend_app", APP_PATH).load_module()
if not hasattr(app_mod, "create_app"):
    raise SystemExit("❌ V backend/app.py chybí create_app()")

# Vytvoř Flask app a vytáhni DB URI
app = app_mod.create_app()

# SQLAlchemy Core (bez závislosti na tvém 'db' objektu)
from sqlalchemy import create_engine, inspect, text

DB_URI = app.config.get("SQLALCHEMY_DATABASE_URI")
if not DB_URI:
    raise SystemExit("❌ SQLALCHEMY_DATABASE_URI není nastaveno v app.config")

engine = create_engine(DB_URI, future=True)

def q_ident(name: str) -> str:
    """Bezpečné quotování identifikátorů pro různé dialekty."""
    d = engine.dialect.name
    if d in ("postgresql", "sqlite"):
        return f'"{name}"'
    elif d in ("mysql", "mariadb"):
        return f"`{name}`"
    return name  # fallback

def backup_sqlite_if_any():
    if not DB_URI.startswith("sqlite:///"):
        return
    db_path = DB_URI.replace("sqlite:///", "", 1)
    if os.path.isfile(db_path):
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = f"{db_path}.wipebak-{ts}"
        os.makedirs(os.path.dirname(backup), exist_ok=True)
        shutil.copy2(db_path, backup)
        print(f"💾 SQLite backup: {backup}")

def pick_table(inspector, candidates: list[str]) -> str | None:
    """Vybere první existující tabulku ze seznamu kandidátů (case-insensitive)."""
    names = inspector.get_table_names()
    lower_to_orig = {n.lower(): n for n in names}
    for cand in candidates:
        n = cand.lower()
        if n in lower_to_orig:
            return lower_to_orig[n]
    return None

def count_rows(conn, table: str | None) -> int | None:
    if not table:
        return None
    try:
        return conn.execute(text(f"SELECT COUNT(*) FROM {q_ident(table)}")).scalar_one()
    except Exception:
        return None

def main():
    backup_sqlite_if_any()

    insp = inspect(engine)
    with engine.begin() as conn:
        # Najdi skutečné názvy tabulek (různé projekty mohou mít 'order'/'orders', 'product'/'products' atd.)
        t_order_item = pick_table(insp, ["order_item", "order_items"])
        t_order      = pick_table(insp, ["order", "orders"])
        t_payment    = pick_table(insp, ["payment", "payments"])
        t_sold       = pick_table(insp, ["sold_product", "sold_products", "sold"])
        t_product    = pick_table(insp, ["product", "products"])
        # Kategorie záměrně NEHLEDÁME a NEMAŽEME

        print("📊 Před mazáním:",
              {k: count_rows(conn, v) for k, v in {
                  "order_item": t_order_item, "order": t_order,
                  "payment": t_payment, "sold_product": t_sold,
                  "product": t_product
              }.items()})

        # SQLite: necháme FK zapnuté, ale mažeme v pořadí children -> parents
        for tbl in [t_order_item, t_order, t_payment, t_sold, t_product]:
            if not tbl:
                continue
            try:
                conn.execute(text(f"DELETE FROM {q_ident(tbl)}"))
                # volitelně: reset autoincrement (SQLite)
                if engine.dialect.name == "sqlite":
                    try:
                        conn.execute(text("DELETE FROM sqlite_sequence WHERE name=:n"), {"n": tbl})
                    except Exception:
                        pass
                print(f"🧹 Smazáno z {tbl}")
            except Exception as e:
                print(f"⚠️  Nepodařilo se smazat {tbl}: {e}")

        print("📊 Po smazání:",
              {k: count_rows(conn, v) for k, v in {
                  "order_item": t_order_item, "order": t_order,
                  "payment": t_payment, "sold_product": t_sold,
                  "product": t_product
              }.items()})

    print("✅ Hotovo. Kategorie zůstaly, ostatní vyčištěno.")

if __name__ == "__main__":
    main()
