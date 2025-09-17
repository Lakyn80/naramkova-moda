# backend/scripts/backfill_payments_from_orders_standalone.py
import os
import sys
import sqlite3
from datetime import datetime

# ── Cesty ────────────────────────────────────────────────────────────────────
THIS_FILE = os.path.abspath(__file__)
SCRIPTS_DIR = os.path.dirname(THIS_FILE)           # .../backend/scripts
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR)         # .../backend
DB_PATH = os.path.join(BACKEND_DIR, "instance", "database.db")

def row_factory(cursor, row):
    """Vrací dict místo tuple."""
    return {d[0]: row[i] for i, d in enumerate(cursor.description)}

def table_exists(conn, name: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name = ?",
        (name,),
    )
    return cur.fetchone() is not None

def pragma_columns(conn, table: str) -> list[str]:
    cur = conn.execute(f"PRAGMA table_info('{table}');")
    return [r["name"] for r in cur.fetchall()]

def detect_order_item_schema(conn):
    if not table_exists(conn, "order_item"):
        return {"has_table": False}
    cols = set(pragma_columns(conn, "order_item"))
    return {
        "has_table": True,
        "fk": "order_id" if "order_id" in cols else None,
        "amount": "amount_czk" if "amount_czk" in cols else None,
        "price": next((c for c in ("price_czk","unit_price_czk","unit_price") if c in cols), None),
        "qty":   next((c for c in ("quantity","qty","count") if c in cols), None),
    }

def compute_amounts(conn, order_ids):
    """Dict {order_id: amount(float)} z order_item podle dostupných sloupců."""
    if not order_ids:
        return {}
    sch = detect_order_item_schema(conn)
    if not sch.get("has_table") or not sch.get("fk"):
        return {}

    qmarks = ",".join(["?"] * len(order_ids))
    if sch.get("amount"):
        sql = f"""
            SELECT {sch['fk']} AS oid, COALESCE(SUM({sch['amount']}), 0) AS total
            FROM order_item
            WHERE {sch['fk']} IN ({qmarks})
            GROUP BY {sch['fk']}
        """
        rows = conn.execute(sql, order_ids).fetchall()
        return {r["oid"]: float(r["total"]) for r in rows}

    if sch.get("price") and sch.get("qty"):
        sql = f"""
            SELECT {sch['fk']} AS oid, COALESCE(SUM({sch['price']} * {sch['qty']}), 0) AS total
            FROM order_item
            WHERE {sch['fk']} IN ({qmarks})
            GROUP BY {sch['fk']}
        """
        rows = conn.execute(sql, order_ids).fetchall()
        return {r["oid"]: float(r["total"]) for r in rows}

    return {}

def ensure_payment_table(conn):
    """Pokud tabulka payment neexistuje, vytvoří minimální schéma, které admin obvykle očekává."""
    if table_exists(conn, "payment"):
        return
    conn.execute("""
        CREATE TABLE payment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vs TEXT NOT NULL,
            status TEXT,
            amount_czk REAL,
            reference TEXT,
            received_at TEXT
        );
    """)
    conn.commit()

def vs_fallback(order_id, vs):
    vs = (vs or "").strip() if isinstance(vs, str) else (str(vs) if vs is not None else "")
    return vs if vs else f"{int(order_id):08d}"

def main():
    if not os.path.exists(DB_PATH):
        print(f"[ERR] DB neexistuje: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = row_factory

    try:
        if not table_exists(conn, "order"):
            print("[ERR] Tabulka 'order' neexistuje v této DB.")
            sys.exit(1)

        ensure_payment_table(conn)

        order_cols = set(pragma_columns(conn, "order"))
        # Bezpečně číst dostupné sloupce
        has_total = "total_czk" in order_cols
        has_status = "status" in order_cols
        has_vs = "vs" in order_cols
        has_created = "created_at" in order_cols

        orders = conn.execute(f"""
            SELECT
                id,
                { 'vs,' if has_vs else 'NULL AS vs,' }
                { 'status,' if has_status else 'NULL AS status,' }
                { 'total_czk,' if has_total else 'NULL AS total_czk,' }
                { 'created_at' if has_created else 'NULL AS created_at' }
            FROM "order"
            ORDER BY id ASC
        """).fetchall()
        if not orders:
            print("No orders found.")
            return

        ids = [o["id"] for o in orders]
        computed = compute_amounts(conn, ids)

        created = 0
        updated = 0

        for o in orders:
            oid = o["id"]
            vs = vs_fallback(oid, o.get("vs"))
            amount = None

            if has_total and o.get("total_czk") is not None:
                try:
                    amount = float(o["total_czk"])
                except Exception:
                    amount = None
            if amount is None:
                amount = computed.get(oid)

            # Najdi poslední payment pro stejné VS
            pay = conn.execute(
                "SELECT id, vs, status, amount_czk, reference, received_at "
                "FROM payment WHERE vs = ? ORDER BY id DESC LIMIT 1",
                (vs,),
            ).fetchone()

            if pay:
                # doplníme chybějící hodnoty
                changed = False
                if amount is not None and (pay["amount_czk"] is None):
                    conn.execute("UPDATE payment SET amount_czk = ? WHERE id = ?", (amount, pay["id"]))
                    changed = True
                if (pay["status"] is None) or (pay["status"] == ""):
                    conn.execute("UPDATE payment SET status = 'pending' WHERE id = ?", (pay["id"],))
                    changed = True
                if (pay["received_at"] is None) and has_created and o.get("created_at"):
                    conn.execute("UPDATE payment SET received_at = ? WHERE id = ?",
                                 (o["created_at"], pay["id"]))
                    changed = True
                if changed:
                    updated += 1
            else:
                received_at = o.get("created_at") if has_created else None
                if received_at is None:
                    received_at = datetime.utcnow().isoformat()
                conn.execute(
                    "INSERT INTO payment (vs, status, amount_czk, reference, received_at) "
                    "VALUES (?, 'pending', ?, ?, ?)",
                    (vs, amount, f"backfill from order #{oid}", received_at),
                )
                created += 1

            # volitelně sjednotíme awaiting_payment u objednávek bez statusu
            if has_status and (o.get("status") is None or o.get("status") == ""):
                conn.execute("UPDATE \"order\" SET status = 'awaiting_payment' WHERE id = ?", (oid,))

        conn.commit()

        total_pay = conn.execute("SELECT COUNT(*) AS c FROM payment").fetchone()["c"]
        print(f"DB: {DB_PATH}")
        print(f"Created payments: {created}, updated existing: {updated}")
        print(f"payment rows total: {total_pay}")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
