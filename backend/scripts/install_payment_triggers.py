# backend/scripts/install_payment_triggers.py
import os, sys, sqlite3

THIS_FILE = os.path.abspath(__file__)
SCRIPTS_DIR = os.path.dirname(THIS_FILE)     # .../backend/scripts
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR)   # .../backend
DB_PATH = os.path.normpath(os.path.join(BACKEND_DIR, "instance", "database.db"))

SQL = r"""
PRAGMA foreign_keys=ON;

-- 1) Po INSERTU do "order": dopočítej VS a založ payment
DROP TRIGGER IF EXISTS trg_order_ai_payment;
CREATE TRIGGER trg_order_ai_payment
AFTER INSERT ON "order"
BEGIN
    UPDATE "order"
    SET vs = COALESCE(NULLIF(TRIM(NEW.vs), ''), printf('%08d', NEW.id))
    WHERE id = NEW.id;

    INSERT INTO payment (vs, status, amount_czk, reference, received_at)
    VALUES (
        COALESCE(NULLIF(TRIM(NEW.vs), ''), printf('%08d', NEW.id)),
        CASE WHEN NEW.status='paid' THEN 'received' ELSE 'pending' END,
        COALESCE(NEW.total_czk, 0),
        'auto: from trigger order insert',
        COALESCE(NEW.created_at, datetime('now'))
    );
END;

-- 2) Propagace změny VS z objednávky do payment
DROP TRIGGER IF EXISTS trg_order_au_vs_propagate;
CREATE TRIGGER trg_order_au_vs_propagate
AFTER UPDATE OF vs ON "order"
WHEN OLD.vs IS NOT NEW.vs
BEGIN
    UPDATE payment
    SET vs = COALESCE(NULLIF(TRIM(NEW.vs), ''), printf('%08d', NEW.id))
    WHERE vs = COALESCE(NULLIF(TRIM(OLD.vs), ''), printf('%08d', NEW.id));
END;

-- 3) Přepočet amount v payment při změně order_item (INSERT/UPDATE/DELETE)
DROP TRIGGER IF EXISTS trg_order_item_ai_recalc_amount;
CREATE TRIGGER trg_order_item_ai_recalc_amount
AFTER INSERT ON order_item
BEGIN
    UPDATE payment
    SET amount_czk = (
        SELECT COALESCE(SUM(
            COALESCE(oi.amount_czk,
                     (COALESCE(oi.price_czk, COALESCE(oi.unit_price_czk, oi.unit_price))
                      * COALESCE(oi.quantity, COALESCE(oi.qty, COALESCE(oi.count,1))))
            )
        ),0)
        FROM order_item oi
        WHERE oi.order_id = NEW.order_id
    )
    WHERE vs = (SELECT COALESCE(NULLIF(TRIM(vs), ''), printf('%08d', id))
                FROM "order" WHERE id = NEW.order_id);
END;

DROP TRIGGER IF EXISTS trg_order_item_au_recalc_amount;
CREATE TRIGGER trg_order_item_au_recalc_amount
AFTER UPDATE ON order_item
BEGIN
    UPDATE payment
    SET amount_czk = (
        SELECT COALESCE(SUM(
            COALESCE(oi.amount_czk,
                     (COALESCE(oi.price_czk, COALESCE(oi.unit_price_czk, oi.unit_price))
                      * COALESCE(oi.quantity, COALESCE(oi.qty, COALESCE(oi.count,1))))
            )
        ),0)
        FROM order_item oi
        WHERE oi.order_id = NEW.order_id
    )
    WHERE vs = (SELECT COALESCE(NULLIF(TRIM(vs), ''), printf('%08d', id))
                FROM "order" WHERE id = NEW.order_id);
END;

DROP TRIGGER IF EXISTS trg_order_item_ad_recalc_amount;
CREATE TRIGGER trg_order_item_ad_recalc_amount
AFTER DELETE ON order_item
BEGIN
    UPDATE payment
    SET amount_czk = (
        SELECT COALESCE(SUM(
            COALESCE(oi.amount_czk,
                     (COALESCE(oi.price_czk, COALESCE(oi.unit_price_czk, oi.unit_price))
                      * COALESCE(oi.quantity, COALESCE(oi.qty, COALESCE(oi.count,1))))
            )
        ),0)
        FROM order_item oi
        WHERE oi.order_id = OLD.order_id
    )
    WHERE vs = (SELECT COALESCE(NULLIF(TRIM(vs), ''), printf('%08d', id))
                FROM "order" WHERE id = OLD.order_id);
END;

-- 4) Změna statusu payment → přepni status order
DROP TRIGGER IF EXISTS trg_payment_au_status_to_paid;
CREATE TRIGGER trg_payment_au_status_to_paid
AFTER UPDATE OF status ON payment
WHEN NEW.status = 'received'
BEGIN
    UPDATE "order" SET status='paid'
    WHERE vs = NEW.vs;
END;

DROP TRIGGER IF EXISTS trg_payment_au_status_to_awaiting;
CREATE TRIGGER trg_payment_au_status_to_awaiting
AFTER UPDATE OF status ON payment
WHEN NEW.status IN ('pending','failed','canceled','refunded')
BEGIN
    UPDATE "order" SET status='awaiting_payment'
    WHERE vs = NEW.vs AND status <> 'paid';
END;
"""

def main():
    if not os.path.exists(DB_PATH):
        print("[ERR] DB not found:", DB_PATH); sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    try:
cat > backend/scripts/install_payment_triggers.py <<'PY'
# backend/scripts/install_payment_triggers.py
import os, sys, sqlite3

THIS_FILE = os.path.abspath(__file__)
SCRIPTS_DIR = os.path.dirname(THIS_FILE)     # .../backend/scripts
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR)   # .../backend
DB_PATH = os.path.normpath(os.path.join(BACKEND_DIR, "instance", "database.db"))

SQL = r"""
PRAGMA foreign_keys=ON;

-- 1) Po INSERTU do "order": dopočítej VS a založ payment
DROP TRIGGER IF EXISTS trg_order_ai_payment;
CREATE TRIGGER trg_order_ai_payment
AFTER INSERT ON "order"
BEGIN
    UPDATE "order"
    SET vs = COALESCE(NULLIF(TRIM(NEW.vs), ''), printf('%08d', NEW.id))
    WHERE id = NEW.id;

    INSERT INTO payment (vs, status, amount_czk, reference, received_at)
    VALUES (
        COALESCE(NULLIF(TRIM(NEW.vs), ''), printf('%08d', NEW.id)),
        CASE WHEN NEW.status='paid' THEN 'received' ELSE 'pending' END,
        COALESCE(NEW.total_czk, 0),
        'auto: from trigger order insert',
        COALESCE(NEW.created_at, datetime('now'))
    );
END;

-- 2) Propagace změny VS z objednávky do payment
DROP TRIGGER IF EXISTS trg_order_au_vs_propagate;
CREATE TRIGGER trg_order_au_vs_propagate
AFTER UPDATE OF vs ON "order"
WHEN OLD.vs IS NOT NEW.vs
BEGIN
    UPDATE payment
    SET vs = COALESCE(NULLIF(TRIM(NEW.vs), ''), printf('%08d', NEW.id))
    WHERE vs = COALESCE(NULLIF(TRIM(OLD.vs), ''), printf('%08d', NEW.id));
END;

-- 3) Přepočet amount v payment při změně order_item (INSERT/UPDATE/DELETE)
DROP TRIGGER IF EXISTS trg_order_item_ai_recalc_amount;
CREATE TRIGGER trg_order_item_ai_recalc_amount
AFTER INSERT ON order_item
BEGIN
    UPDATE payment
    SET amount_czk = (
        SELECT COALESCE(SUM(
            COALESCE(oi.amount_czk,
                     (COALESCE(oi.price_czk, COALESCE(oi.unit_price_czk, oi.unit_price))
                      * COALESCE(oi.quantity, COALESCE(oi.qty, COALESCE(oi.count,1))))
            )
        ),0)
        FROM order_item oi
        WHERE oi.order_id = NEW.order_id
    )
    WHERE vs = (SELECT COALESCE(NULLIF(TRIM(vs), ''), printf('%08d', id))
                FROM "order" WHERE id = NEW.order_id);
END;

DROP TRIGGER IF EXISTS trg_order_item_au_recalc_amount;
CREATE TRIGGER trg_order_item_au_recalc_amount
AFTER UPDATE ON order_item
BEGIN
    UPDATE payment
    SET amount_czk = (
        SELECT COALESCE(SUM(
            COALESCE(oi.amount_czk,
                     (COALESCE(oi.price_czk, COALESCE(oi.unit_price_czk, oi.unit_price))
                      * COALESCE(oi.quantity, COALESCE(oi.qty, COALESCE(oi.count,1))))
            )
        ),0)
        FROM order_item oi
        WHERE oi.order_id = NEW.order_id
    )
    WHERE vs = (SELECT COALESCE(NULLIF(TRIM(vs), ''), printf('%08d', id))
                FROM "order" WHERE id = NEW.order_id);
END;

DROP TRIGGER IF EXISTS trg_order_item_ad_recalc_amount;
CREATE TRIGGER trg_order_item_ad_recalc_amount
AFTER DELETE ON order_item
BEGIN
    UPDATE payment
    SET amount_czk = (
        SELECT COALESCE(SUM(
            COALESCE(oi.amount_czk,
                     (COALESCE(oi.price_czk, COALESCE(oi.unit_price_czk, oi.unit_price))
                      * COALESCE(oi.quantity, COALESCE(oi.qty, COALESCE(oi.count,1))))
            )
        ),0)
        FROM order_item oi
        WHERE oi.order_id = OLD.order_id
    )
    WHERE vs = (SELECT COALESCE(NULLIF(TRIM(vs), ''), printf('%08d', id))
                FROM "order" WHERE id = OLD.order_id);
END;

-- 4) Změna statusu payment → přepni status order
DROP TRIGGER IF EXISTS trg_payment_au_status_to_paid;
CREATE TRIGGER trg_payment_au_status_to_paid
AFTER UPDATE OF status ON payment
WHEN NEW.status = 'received'
BEGIN
    UPDATE "order" SET status='paid'
    WHERE vs = NEW.vs;
END;

DROP TRIGGER IF EXISTS trg_payment_au_status_to_awaiting;
CREATE TRIGGER trg_payment_au_status_to_awaiting
AFTER UPDATE OF status ON payment
WHEN NEW.status IN ('pending','failed','canceled','refunded')
BEGIN
    UPDATE "order" SET status='awaiting_payment'
    WHERE vs = NEW.vs AND status <> 'paid';
END;
"""

def main():
    if not os.path.exists(DB_PATH):
        print("[ERR] DB not found:", DB_PATH); sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    try:


git add backend/scripts/install_payment_triggers.py backend/scripts/backfill_payments_from_orders_standalone.py
git commit -m "Add payments backfill + SQLite triggers installer"

# před tím zavři DB Browser a (pro jistotu) zastav backend
python backend/scripts/install_payment_triggers.py
# očekávej: "Triggers installed OK -> .../backend/instance/database.db"


cat > backend/scripts/install_payment_triggers.py <<'PY'
# backend/scripts/install_payment_triggers.py
import os, sys, sqlite3

THIS_FILE = os.path.abspath(__file__)
SCRIPTS_DIR = os.path.dirname(THIS_FILE)     # .../backend/scripts
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR)   # .../backend
DB_PATH = os.path.normpath(os.path.join(BACKEND_DIR, "instance", "database.db"))

SQL = r"""
PRAGMA foreign_keys=ON;

-- 1) Po INSERTU do "order": dopočítej VS a založ payment
DROP TRIGGER IF EXISTS trg_order_ai_payment;
CREATE TRIGGER trg_order_ai_payment
AFTER INSERT ON "order"
BEGIN
    UPDATE "order"
    SET vs = COALESCE(NULLIF(TRIM(NEW.vs), ''), printf('%08d', NEW.id))
    WHERE id = NEW.id;

    INSERT INTO payment (vs, status, amount_czk, reference, received_at)
    VALUES (
        COALESCE(NULLIF(TRIM(NEW.vs), ''), printf('%08d', NEW.id)),
        CASE WHEN NEW.status='paid' THEN 'received' ELSE 'pending' END,
        COALESCE(NEW.total_czk, 0),
        'auto: from trigger order insert',
        COALESCE(NEW.created_at, datetime('now'))
    );
END;

-- 2) Propagace změny VS z objednávky do payment
DROP TRIGGER IF EXISTS trg_order_au_vs_propagate;
CREATE TRIGGER trg_order_au_vs_propagate
AFTER UPDATE OF vs ON "order"
WHEN OLD.vs IS NOT NEW.vs
BEGIN
    UPDATE payment
    SET vs = COALESCE(NULLIF(TRIM(NEW.vs), ''), printf('%08d', NEW.id))
    WHERE vs = COALESCE(NULLIF(TRIM(OLD.vs), ''), printf('%08d', NEW.id));
END;

-- 3) Přepočet amount v payment při změně order_item (INSERT/UPDATE/DELETE)
DROP TRIGGER IF EXISTS trg_order_item_ai_recalc_amount;
CREATE TRIGGER trg_order_item_ai_recalc_amount
AFTER INSERT ON order_item
BEGIN
    UPDATE payment
    SET amount_czk = (
        SELECT COALESCE(SUM(
            COALESCE(oi.amount_czk,
                     (COALESCE(oi.price_czk, COALESCE(oi.unit_price_czk, oi.unit_price))
                      * COALESCE(oi.quantity, COALESCE(oi.qty, COALESCE(oi.count,1))))
            )
        ),0)
        FROM order_item oi
        WHERE oi.order_id = NEW.order_id
    )
    WHERE vs = (SELECT COALESCE(NULLIF(TRIM(vs), ''), printf('%08d', id))
                FROM "order" WHERE id = NEW.order_id);
END;

DROP TRIGGER IF EXISTS trg_order_item_au_recalc_amount;
CREATE TRIGGER trg_order_item_au_recalc_amount
AFTER UPDATE ON order_item
BEGIN
    UPDATE payment
    SET amount_czk = (
        SELECT COALESCE(SUM(
            COALESCE(oi.amount_czk,
                     (COALESCE(oi.price_czk, COALESCE(oi.unit_price_czk, oi.unit_price))
                      * COALESCE(oi.quantity, COALESCE(oi.qty, COALESCE(oi.count,1))))
            )
        ),0)
        FROM order_item oi
        WHERE oi.order_id = NEW.order_id
    )
    WHERE vs = (SELECT COALESCE(NULLIF(TRIM(vs), ''), printf('%08d', id))
                FROM "order" WHERE id = NEW.order_id);
END;

DROP TRIGGER IF EXISTS trg_order_item_ad_recalc_amount;
CREATE TRIGGER trg_order_item_ad_recalc_amount
AFTER DELETE ON order_item
BEGIN
    UPDATE payment
    SET amount_czk = (
        SELECT COALESCE(SUM(
            COALESCE(oi.amount_czk,
                     (COALESCE(oi.price_czk, COALESCE(oi.unit_price_czk, oi.unit_price))
                      * COALESCE(oi.quantity, COALESCE(oi.qty, COALESCE(oi.count,1))))
            )
        ),0)
        FROM order_item oi
        WHERE oi.order_id = OLD.order_id
    )
    WHERE vs = (SELECT COALESCE(NULLIF(TRIM(vs), ''), printf('%08d', id))
                FROM "order" WHERE id = OLD.order_id);
END;

-- 4) Změna statusu payment → přepni status order
DROP TRIGGER IF EXISTS trg_payment_au_status_to_paid;
CREATE TRIGGER trg_payment_au_status_to_paid
AFTER UPDATE OF status ON payment
WHEN NEW.status = 'received'
BEGIN
    UPDATE "order" SET status='paid'
    WHERE vs = NEW.vs;
END;

DROP TRIGGER IF EXISTS trg_payment_au_status_to_awaiting;
CREATE TRIGGER trg_payment_au_status_to_awaiting
AFTER UPDATE OF status ON payment
WHEN NEW.status IN ('pending','failed','canceled','refunded')
BEGIN
    UPDATE "order" SET status='awaiting_payment'
    WHERE vs = NEW.vs AND status <> 'paid';
END;
"""

def main():
    if not os.path.exists(DB_PATH):
        print("[ERR] DB not found:", DB_PATH); sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SQL)
        conn.commit()
        print("Triggers installed OK ->", DB_PATH)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
