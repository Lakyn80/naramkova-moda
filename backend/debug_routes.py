# backend/debug_routes.py
from flask import Blueprint, jsonify
from backend.extensions import db
from backend.config import _resolve_sqlite_uri
import os
import datetime as dt

debug_bp = Blueprint("debug_bp", __name__, url_prefix="/debug")

@debug_bp.get("/db")
def debug_db():
    # Co je v env a co resolver vrací
    raw_env_url = os.getenv("DATABASE_URL")
    resolved_url = _resolve_sqlite_uri(raw_env_url)

    # Co si SQLAlchemy myslí a co SQLite skutečně otevřel
    engine_url = str(db.engine.url)
    pragma = db.session.execute(db.text("PRAGMA database_list;")).fetchall()
    database_list = [dict(r._mapping) for r in pragma]
    main_path = next((d["file"] for d in database_list if d.get("name") == "main"), None)

    file_info = None
    if main_path and os.path.exists(main_path):
        st = os.stat(main_path)
        file_info = {
            "exists": True,
            "path": main_path,
            "size_bytes": st.st_size,
            "mtime": dt.datetime.fromtimestamp(st.st_mtime).isoformat(),
        }
    else:
        file_info = {"exists": False, "path": main_path}

    # Seznam tabulek
    tables = db.session.execute(
        db.text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    ).fetchall()
    table_names = [t[0] for t in tables]

    # Počty řádků v kandidátních tabulkách
    def safe_count(name: str):
        try:
            return db.session.execute(db.text(f"SELECT COUNT(*) FROM {name}")).scalar_one()
        except Exception:
            return None

    counts = {name: safe_count(name) for name in ("payments", "payment")}

    # Ukázka záznamů (pokud jsou)
    sample = {}
    for name in ("payments", "payment"):
        if counts.get(name):
            for cols in (
                "id, vs, status, amount, received_at",
                "id, status, amount",
                "id",
            ):
                try:
                    rows = db.session.execute(
                        db.text(f"SELECT {cols} FROM {name} ORDER BY id DESC LIMIT 5")
                    ).fetchall()
                    sample[name] = {
                        "columns": cols,
                        "rows": [dict(r._mapping) for r in rows],
                    }
                    break
                except Exception:
                    continue

    return jsonify({
        "env_DATABASE_URL": raw_env_url,
        "resolved_uri": resolved_url,
        "engine_url": engine_url,
        "database_list": database_list,
        "file_info": file_info,
        "tables": table_names,
        "counts": counts,
        "sample": sample,
    })
