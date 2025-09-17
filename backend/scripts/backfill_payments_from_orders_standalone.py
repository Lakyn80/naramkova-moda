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
    # Každý SELECT vrací dict {col_name: value}
    return {d[0]: row[i] for i, d in enumerate(cursor.description)}

def table_exists(conn, name: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name = ?",
        (name,),
    )
    return cur.fetchone() is not None

def pragma_table_info(conn, table: str):
    # Vzhledem k row_factory už dostáváme list[dict]
    return conn.execute(f"PRAGMA table_info('{table}');").fetchall()

def detect_order_item_schema(conn):
    if not table_exists(conn, "order_item"):
        return {"has_table": False}
    cols = {c["name"] for c in pragma_table_info(conn, "order_item")}
    return {
        "has_table": True,
        "fk": "order_id" if "order_id" in cols else None,
        "amount": "amount_czk" if "amount_czk" in cols else None,
        "price": next((c for c in ("price_czk","unit_price_czk","unit_price") if c in cols), None),
        "qty":   next((c for c in ("quantity","qty","count") if c in cols), None),
    }

def compute_amounts(conn, order_ids):
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
    # Pokud tabulka/VIEW 'payment' chybí, vytvoříme minimální tabulku s NOT NULL amount (default 0)
    if table_exists(conn, "payment"):
        return
    conn.execute("""
        CREATE TABLE payment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vs TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            amount_czk REAL NOT NULL DEFAULT 0,
            reference TEXT,
            received_at TEXT
        );
    """)
    conn.commit()

def payment_schema(conn):
    info = pragma_table_info(conn, "payment")  # list[dict]
    cols = {r["name"] for r in info}
    amount_col = "amount_czk" if "amount_czk" in cols else ("amount" if "amount" in cols else None)
    return {"cols": cols, "amount_col": amount_col}

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

        pay_sch = payment_schema(conn)
        pay_cols = pay_sch["cols"]
        amount_col = pay_sch["amount_col"]
        if amount_col is None:
            print("[ERR] V 'payment' není sloupec 'amount_czk' ani 'amount'.")
            sys.exit(1)

        order_cols = {c["name"] for c in pragma_table_info(conn, "order")}
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

            # dopočti částku
            amount = None
            if has_total and o.get("total_czk") is not None:
                try:
                    amount = float(o["total_czk"])
                except Exception:
                    amount = None
            if amount is None:
                amount = computed.get(oid)
            if amount is None:
                amount = 0.0  # nikdy neposílej NULL do NOT NULL

            # hledej poslední payment pro stejné VS
            pay = conn.execute(
                f"SELECT id, vs, status, {amount_col} AS amount_val, reference, received_at "
                f"FROM payment WHERE vs = ? ORDER BY id DESC LIMIT 1",
                (vs,),
            ).fetchone()

            if pay:
                changed = False
                if (pay["amount_val"] is None) or (pay["amount_val"] == 0):
                    conn.execute(f"UPDATE payment SET {amount_col} = ? WHERE id = ?", (amount, pay["id"]))
                    changed = True
                if ("status" in pay_cols) and (pay.get("status") in (None, "")):
                    conn.execute("UPDATE payment SET status = 'pending' WHERE id = ?", (pay["id"],))
                    changed = True
                if ("received_at" in pay_cols) and (pay.get("received_at") is None):
                    recv = o.get("created_at") if has_created else None
                    if recv is None:
                        recv = datetime.utcnow().isoformat()
                    conn.execute("UPDATE payment SET received_at = ? WHERE id = ?", (recv, pay["id"]))
                    changed = True
                if changed:
                    updated += 1
            else:
                # vlož nový payment (dynamicky podle dostupných sloupců)
                fields = ["vs"]
                values = [vs]
                placeholders = ["?"]

                if "status" in pay_cols:
                    fields.append("status");       placeholders.append("?"); values.append("pending")
                fields.append(amount_col);         placeholders.append("?"); values.append(amount)
                if "reference" in pay_cols:
                    fields.append("reference");   placeholders.append("?"); values.append(f"backfill from order #{oid}")
                if "received_at" in pay_cols:
                    recv = o.get("created_at") if has_created else None
                    if recv is None:
                        recv = datetime.utcnow().isoformat()
                    fields.append("received_at"); placeholders.append("?"); values.append(recv)

                sql = f"INSERT INTO payment ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
                conn.execute(sql, values)
                created += 1

            # volitelně sjednoť prázdný status u order
            if has_status and (o.get("status") in (None, "")):
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
