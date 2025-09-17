# backend/api/routes/payment_routes.py
import io
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from flask import Blueprint, request, jsonify, current_app, send_file
import qrcode
from backend.extensions import db
from backend.admin.models import Order, Payment
from backend.api.utils.csob_mail_sync import fetch_csob_incoming, fetch_from_imap
from backend.api.utils.telegram import send_telegram_message



payment_bp = Blueprint("payment_bp", __name__, url_prefix="/api/payments")


# --- Helpers ---------------------------------------------------------------

def _get_iban() -> str:
    """IBAN obchodníka (ENV MERCHANT_IBAN > Flask config MERCHANT_IBAN)."""
    iban = os.getenv("MERCHANT_IBAN") or current_app.config.get("MERCHANT_IBAN")
    if not iban:
        raise RuntimeError("MERCHANT_IBAN není nastaven (ENV nebo Config).")
    return iban.replace(" ", "").upper()


def _to_decimal(val) -> Decimal:
    """Bezpečný převod na Decimal; vyhazuje InvalidOperation na neplatnou hodnotu."""
    return Decimal(str(val))


def _build_spd_payload(iban: str, amount: Decimal, vs: str | None, msg: str | None) -> str:
    """
    SPD 1.0 payload pro české QR platby (CZK):
    SPD*1.0*ACC:...*AM:...*CC:CZK*X-VS:...*MSG:...
    """
    parts = ["SPD*1.0", f"ACC:{iban}", f"AM:{amount:.2f}", "CC:CZK"]
    if vs:
        parts.append(f"X-VS:{vs}")
    if msg:
        # SPD povoluje ASCII; vynecháme diakritiku/emoji a zkrátíme.
        safe_msg = "".join(ch for ch in (msg or "") if 32 <= ord(ch) <= 126)
        parts.append(f"MSG:{safe_msg[:60]}")
    return "*".join(parts)


def _safe_int(value, default):
    """Bezpečný převod na int s dolní hranicí 0."""
    try:
        v = int(value)
        return v if v >= 0 else default
    except Exception:
        return default


def _detect_order_item_schema():
    """
    Prohlédne schéma tabulky 'order_item' a vrátí slovník s tím,
    jaké sloupce jsou k dispozici pro výpočet součtu.
    """
    cols = db.session.execute(db.text("PRAGMA table_info('order_item');")).fetchall()
    colnames = {c[1] for c in cols}

    # kandidáti pro jednotkovou cenu
    price_cols = [c for c in ("price_czk", "unit_price_czk", "unit_price") if c in colnames]
    # kandidáti pro množství
    qty_cols = [c for c in ("quantity", "qty", "count") if c in colnames]
    # přímý sloupec s částkou položky (fallback)
    amount_cols = [c for c in ("amount_czk",) if c in colnames]

    # název FK na order (typicky order_id)
    fk_col = "order_id" if "order_id" in colnames else None

    return {
        "has_table": len(cols) > 0,
        "price_cols": price_cols,
        "qty_cols": qty_cols,
        "amount_cols": amount_cols,
        "fk_col": fk_col,
    }


def _compute_amounts_for_orders(order_ids):
    """
    Vrátí dict {order_id: sum_amount} sečtený z 'order_item'.
    Pokud nelze spočítat (chybějící tabulka/sloupce), vrátí prázdný dict.
    """
    if not order_ids:
        return {}

    schema = _detect_order_item_schema()
    if not schema["has_table"] or not schema["fk_col"]:
        return {}

    fk = schema["fk_col"]
    # Pokus 1: amount_czk přímo
    if schema["amount_cols"]:
        amount_col = schema["amount_cols"][0]
        sql = f"""
            SELECT {fk} as oid, COALESCE(SUM({amount_col}), 0) AS total
            FROM order_item
            WHERE {fk} IN :ids
            GROUP BY {fk}
        """
        rows = db.session.execute(
            db.text(sql.replace(":ids", "(:ids)")),
            {"ids": tuple(order_ids)},
        ).fetchall()
        return {r.oid: float(r.total) for r in rows}

    # Pokus 2: price * qty
    if schema["price_cols"] and schema["qty_cols"]:
        price = schema["price_cols"][0]
        qty = schema["qty_cols"][0]
        sql = f"""
            SELECT {fk} as oid, COALESCE(SUM({price} * {qty}), 0) AS total
            FROM order_item
            WHERE {fk} IN :ids
            GROUP BY {fk}
        """
        rows = db.session.execute(
            db.text(sql.replace(":ids", "(:ids)")),
            {"ids": tuple(order_ids)},
        ).fetchall()
        return {r.oid: float(r.total) for r in rows}

    return {}


def _vs_display(vs, order_id):
    """
    VS pro výstup: pokud vs je prázdné/NULL, použij fallback z id (osmimístný).
    DB se tímto NEUPRAVUJE.
    """
    vs = (vs or "").strip()
    return vs if vs else f"{int(order_id):08d}"


# --- DOPLNĚNO: Poštovné a porovnání částek ---------------------------------

def _shipping_fee() -> Decimal:
    """
    Poštovné v CZK:
    1) ENV SHIPPING_FEE_CZK
    2) current_app.config["SHIPPING_FEE_CZK"]
    3) default 89.00
    """
    raw = os.getenv("SHIPPING_FEE_CZK")
    if raw is None:
        raw = current_app.config.get("SHIPPING_FEE_CZK", "89.00")
    try:
        return _to_decimal(raw)
    except InvalidOperation:
        return Decimal("89.00")


def _amounts_equal(a: Decimal, b: Decimal, tol: Decimal = Decimal("0.50")) -> bool:
    """Porovnání s tolerancí (např. odchylky/zaokrouhlení)."""
    return abs(_to_decimal(a) - _to_decimal(b)) <= _to_decimal(tol)


def _order_base_amount_czk(order: Order) -> Decimal | None:
    """
    Základní částka objednávky (bez poštovného):
    - přednostně Order.total_czk (pokud je)
    - jinak dopočítat z order_item pomocí _compute_amounts_for_orders
    """
    total = getattr(order, "total_czk", None)
    if total is not None:
        try:
            return _to_decimal(total)
        except InvalidOperation:
            return None

    comp = _compute_amounts_for_orders([order.id])
    if comp.get(order.id) is not None:
        try:
            return _to_decimal(comp[order.id])
        except InvalidOperation:
            return None
    return None


# --- QR endpoints ----------------------------------------------------------

@payment_bp.get("/qr")
def payment_qr_png():
    """
    GET /api/payments/qr?amount=1234.00&vs=20250814&msg=Objednavka%20123
    Vrací PNG s QR kódem (MIME image/png).
    """
    try:
        amount_raw = (request.args.get("amount") or "").strip()
        if not amount_raw:
            return jsonify({"ok": False, "error": "Chybí query param 'amount'."}), 400

        try:
            amount = _to_decimal(amount_raw)
        except InvalidOperation:
            return jsonify({"ok": False, "error": "Neplatná částka 'amount'."}), 400
        if amount <= 0:
            return jsonify({"ok": False, "error": "Částka musí být > 0."}), 400

        vs = (request.args.get("vs") or "").strip() or None
        msg = (request.args.get("msg") or "").strip() or None

        iban = _get_iban()
        payload = _build_spd_payload(iban, amount, vs, msg)

        img = qrcode.make(payload)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        return send_file(
            buf,
            mimetype="image/png",
            as_attachment=False,
            download_name="qr-platba.png",
            max_age=60,
            etag=False,
            last_modified=None,
        )
    except Exception as e:
        current_app.logger.exception("QR platba selhala")
        return jsonify({"ok": False, "error": str(e)}), 500


@payment_bp.get("/qr/payload")
def payment_qr_payload():
    """GET /api/payments/qr/payload?amount=...&vs=...&msg=... → JSON s SPD payloadem."""
    try:
        amount_raw = (request.args.get("amount") or "").strip()
        if not amount_raw:
            return jsonify({"ok": False, "error": "Chybí query param 'amount'."}), 400
        try:
            amount = _to_decimal(amount_raw)
        except InvalidOperation:
            return jsonify({"ok": False, "error": "Neplatná částka 'amount'."}), 400
        if amount <= 0:
            return jsonify({"ok": False, "error": "Částka musí být > 0."}), 400

        vs = (request.args.get("vs") or "").strip() or None
        msg = (request.args.get("msg") or "").strip() or None

        iban = _get_iban()
        payload = _build_spd_payload(iban, amount, vs, msg)
        return jsonify({"ok": True, "iban": iban, "amount": float(amount), "payload": payload})
    except Exception as e:
        current_app.logger.exception("QR payload selhal")
        return jsonify({"ok": False, "error": str(e)}), 500


# --- NOVÉ: Čtení plateb z tabulky ORDER (pro UI) ---------------------------

@payment_bp.get("/summary")
def payments_summary():
    """
    Souhrn „plateb“ z tabulky Order.
    - count
    - sample (max 5 řádků) s mapováním: id, vs, status, amount, received_at
      * amount = Order.total_czk nebo součet order_item (pokud total_czk je NULL)
      * vs     = Order.vs nebo fallback z id (osmimístné)
    """
    try:
        total = db.session.query(Order).count()

        # sample 5 nejnovějších podle id
        items = (
            db.session.query(Order)
            .order_by(Order.id.desc())
            .limit(5)
            .all()
        )

        ids = [o.id for o in items]
        # pokud total_czk chybí, dopočítáme z order_item
        computed = _compute_amounts_for_orders(ids) if ids else {}

        def map_order(o: Order):
            vs_out = _vs_display(getattr(o, "vs", None), o.id)
            total_czk = getattr(o, "total_czk", None)
            amount_val = (float(total_czk) if total_czk is not None else computed.get(o.id))
            created_at = getattr(o, "created_at", None)
            return {
                "id": o.id,
                "vs": vs_out,
                "status": getattr(o, "status", None),
                "amount": amount_val,
                "received_at": (created_at.isoformat() if created_at else None),
            }

        sample = [map_order(o) for o in items]

        columns_present = []
        for attr in ("id", "vs", "status", "total_czk", "created_at"):
            columns_present.append(attr if hasattr(Order, attr) else f"!missing:{attr}")

        return jsonify({
            "ok": True,
            "source_table": "Order",
            "count": total,
            "sample": sample,
            "columns_present": columns_present,
        })
    except Exception as e:
        current_app.logger.exception("payments_summary (Order) failed")
        return jsonify({"ok": False, "error": str(e)}), 500


@payment_bp.get("")
def payments_list():
    """
    Stránkovaný seznam „plateb“ z Order.
    Query:
      - page (default 1)
      - per_page (default 20, max 200)
      - status (optional, Order.status)
      - sort (optional: 'id','vs','status','amount','received_at','created_at','total_czk'; default 'id')
      - direction ('asc' | 'desc', default 'desc')
    """
    try:
        page = _safe_int(request.args.get("page", 1), 1)
        per_page = min(max(_safe_int(request.args.get("per_page", 20), 20), 1), 200)
        status = (request.args.get("status") or "").strip() or None
        sort = (request.args.get("sort") or "id").strip()
        direction = (request.args.get("direction") or "desc").strip().lower()
        if direction not in ("asc", "desc"):
            direction = "desc"

        q = db.session.query(Order)
        if status and hasattr(Order, "status"):
            q = q.filter(Order.status == status)

        # Sort map (amount -> total_czk, received_at -> created_at)
        sort_map = {
            "id": getattr(Order, "id", None),
            "vs": getattr(Order, "vs", None),
            "status": getattr(Order, "status", None),
            "amount": getattr(Order, "total_czk", None),
            "total_czk": getattr(Order, "total_czk", None),
            "received_at": getattr(Order, "created_at", None),
            "created_at": getattr(Order, "created_at", None),
        }
        sort_col = sort_map.get(sort) or sort_map["id"]
        q = q.order_by(sort_col.asc() if direction == "asc" else sort_col.desc())

        total = q.count()
        items = q.limit(per_page).offset((page - 1) * per_page).all()
        ids = [o.id for o in items]
        computed = _compute_amounts_for_orders(ids) if ids else {}

        def map_order(o: Order):
            vs_out = _vs_display(getattr(o, "vs", None), o.id)
            total_czk = getattr(o, "total_czk", None)
            amount_val = (float(total_czk) if total_czk is not None else computed.get(o.id))
            created_at = getattr(o, "created_at", None)
            return {
                "id": o.id,
                "vs": vs_out,
                "status": getattr(o, "status", None),
                "amount": amount_val,
                "received_at": (created_at.isoformat() if created_at else None),
            }

        items_out = [map_order(o) for o in items]

        return jsonify({
            "ok": True,
            "source_table": "Order",
            "page": page,
            "per_page": per_page,
            "total": total,
            "items": items_out,
            "sort": {"column": sort, "direction": direction},
        })
    except Exception as e:
        current_app.logger.exception("payments_list (Order) failed")
        return jsonify({"ok": False, "error": str(e)}), 500


# --- Platby / párování -----------------------------------------------------

@payment_bp.post("/mark-paid")
def mark_paid_by_vs():
    """
    Potvrzení přijetí platby podle VS (idempotentní).
    Body JSON: { "vs": "123456", "amountCzk": 1234.00, "reference": "FIO 2025-08-14" }
    - pokud Payment(VS) existuje → nastaví 'received', doplní částku/reference
    - jinak vytvoří nový Payment(received)
    - pokud existuje Order(VS) → nastaví Order.status='paid'
    """
    try:
        data = request.get_json(force=True) or {}
        vs = str(data.get("vs", "")).strip()
        if not vs:
            return jsonify({"ok": False, "error": "Chybí VS."}), 400

        # amount je volitelný
        amount = None
        amount_in = data.get("amountCzk", None)
        if amount_in is not None and str(amount_in).strip() != "":
            try:
                amount = _to_decimal(amount_in)
                if amount < 0:
                    return jsonify({"ok": False, "error": "Částka nesmí být záporná."}), 400
            except InvalidOperation:
                return jsonify({"ok": False, "error": "Neplatná částka 'amountCzk'."}), 400

        ref = str(data.get("reference", "") or "").strip()
        if len(ref) > 255:
            ref = ref[:255]

        pay = Payment.query.filter_by(vs=vs).order_by(Payment.id.desc()).first()

        if pay:
            pay.status = "received"
            if amount is not None:
                setattr(pay, "amount_czk", amount)
            if ref:
                pay.reference = (f"{pay.reference} | {ref}" if pay.reference else ref)
            if getattr(pay, "received_at", None) is None:
                pay.received_at = datetime.utcnow()
            created = False
        else:
            pay = Payment(
                vs=vs,
                status="received",
                amount_czk=(amount if amount is not None else None),
                reference=(ref or None),
                received_at=datetime.utcnow(),
            )
            db.session.add(pay)
            created = True

        order = Order.query.filter_by(vs=vs).first()
        if order:
            order.status = "paid"

        db.session.commit()

        return jsonify({
            "ok": True,
            "created": created,
            "paymentId": pay.id,
            "orderId": (order.id if order else None),
            "status": "received"
        }), (201 if created else 200)

    except Exception as e:
        current_app.logger.exception("mark_paid_by_vs failed")
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@payment_bp.post("/sync-from-orders")
def sync_from_orders():
    """
    Backfill: pro všechny Order.status='awaiting_payment' bez existujícího Payment stejného VS
    založí Payment(status='pending', amount_czk=order.total_czk).
    Bezpečné proti NULL VS / NULL total_czk.
    """
    try:
        created = 0
        q = (
            db.session.query(Order)
            .outerjoin(Payment, Payment.vs == Order.vs)
            .filter(
                Order.status == "awaiting_payment",
                Order.vs.isnot(None),
                Order.vs != "",
                Order.total_czk.isnot(None),
                Payment.id.is_(None),
            )
        )
        for o in q.all():
            db.session.add(
                Payment(
                    vs=o.vs,
                    amount_czk=o.total_czk,
                    status="pending",
                    reference=f"auto-sync order #{o.id}",
                )
            )
            created += 1

        if created:
            db.session.commit()

        return jsonify({"ok": True, "created": created}), 200
    except Exception as e:
        current_app.logger.exception("sync_from_orders failed")
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@payment_bp.get("/status/by-vs/<vs>")
def get_status_by_vs(vs: str):
    """
    Jednoduchý status endpoint pro front-end (díky/thank-you stránka apod.).
    Vrací poslední payment a navázanou objednávku (pokud existují).
    """
    try:
        vs = (vs or "").strip()
        if not vs:
            return jsonify({"ok": False, "error": "Chybí VS."}), 400

        pay = Payment.query.filter_by(vs=vs).order_by(Payment.id.desc()).first()
        order = Order.query.filter_by(vs=vs).first()

        return jsonify({
            "ok": True,
            "payment": None if not pay else {
                "id": pay.id,
                "vs": pay.vs,
                "amountCzk": (float(getattr(pay, "amount_czk")) if getattr(pay, "amount_czk", None) is not None else None),
                "status": pay.status,
                "reference": getattr(pay, "reference", None),
                "received_at": (pay.received_at.isoformat() if getattr(pay, "received_at", None) else None),
            },
            "order": None if not order else {
                "id": order.id,
                "status": getattr(order, "status", None),
                "totalCzk": (float(getattr(order, "total_czk")) if getattr(order, "total_czk", None) is not None else None),
                "created_at": (order.created_at.isoformat() if getattr(order, "created_at", None) else None),
            }
        }), 200

    except Exception as e:
        current_app.logger.exception("get_status_by_vs failed")
        return jsonify({"ok": False, "error": str(e)}), 500

@payment_bp.post("/sync-csob-mail")
def sync_csob_mail():
    """
    Ruční sync: načte notifikační e-maily z IMAPu, spáruje podle VS a označí objednávku jako 'paid'.
    Používá výhradně bankovní odesílatele pro změny v DB.
    Navíc vrátí diagnostiku z vlastních mailů (nepáruje).
    """
    try:
        # volitelné override z body
        cfg = request.get_json(silent=True) or {}
        host     = cfg.get("host")
        port     = cfg.get("port")
        ssl      = cfg.get("ssl")
        user     = cfg.get("user")
        password = cfg.get("password")
        folder   = cfg.get("folder") or "INBOX"
        max_     = cfg.get("max", 50)

        bank_senders = cfg.get("bank_senders") or [
            "csob.cz","noreply@csob.cz","no-reply@csob.cz","notification@csob.cz","info@csob.cz"
        ]
        self_senders = cfg.get("self_senders") or [
            "noreply@naramkovamoda.cz","naramkovamoda@email.cz"
        ]

        # 1) BANKA – tohle jediný používáme k párování
        bank_pairs = fetch_csob_incoming(
            host=host, port=port, ssl=ssl, user=user, password=password, folder=folder,
            max_items=max_, bank_senders=bank_senders, mark_seen=True,
        )

        processed = []
        unmatched = []
        fee = _shipping_fee()

        for vs, amount in bank_pairs:
            order = Order.query.filter_by(vs=str(vs)).first()
            if not order:
                unmatched.append({
                    "vs": str(vs),
                    "reason": "order_not_found",
                    "paid": float(amount),
                })
                continue

            # === NOVĚ: očekávaná částka = primárně order.total_czk; fallback base+fee ===
            expected_dec = None
            total_czk_val = getattr(order, "total_czk", None)
            if total_czk_val is not None:
                try:
                    expected_dec = _to_decimal(total_czk_val)
                except InvalidOperation:
                    expected_dec = None

            if expected_dec is None:
                base = _order_base_amount_czk(order)
                if base is None:
                    unmatched.append({
                        "vs": str(vs),
                        "reason": "order_amount_missing",
                        "paid": float(amount),
                    })
                    continue
                expected_dec = _to_decimal(base) + fee

            paid_dec = _to_decimal(amount)

            if _amounts_equal(paid_dec, expected_dec):
                # idempotence
                if order.status != "paid":
                    order.status = "paid"

                pay = Payment.query.filter_by(vs=str(vs)).order_by(Payment.id.desc()).first()
                if pay:
                    pay.status = "received"
                    pay.amount_czk = paid_dec
                    if getattr(pay, "received_at", None) is None:
                        pay.received_at = datetime.utcnow()
                else:
                    pay = Payment(vs=str(vs), amount_czk=paid_dec, status="received", received_at=datetime.utcnow())
                    db.session.add(pay)

                processed.append({
                    "vs": str(vs),
                    "amount": float(paid_dec),
                    "expected": float(expected_dec),
                    "orderId": order.id
                })
            else:
                unmatched.append({
                    "vs": str(vs),
                    "reason": "amount_mismatch",
                    "paid": float(paid_dec),
                    "expected": float(expected_dec),
                    "orderId": order.id,
                })

        if processed:
            db.session.commit()
            # Telegram shrnutí
            lines = [f"✅ Přijata platba VS {p['vs']} • {p['amount']:.2f} CZK (oček. {p['expected']:.2f}) • objednávka #{p['orderId']}" for p in processed]
            try:
                send_telegram_message("\n".join(lines))
            except Exception:
                current_app.logger.exception("Telegram notify failed")

        # 2) DIAGNOSTIKA – naše vlastní notifikace (nepárujeme, jen zobrazíme nalezené VS/částky)
        try:
            self_rows = fetch_from_imap(
                host=host or os.getenv("IMAP_HOST", "imap.seznam.cz"),
                port=int(port or os.getenv("IMAP_PORT", "993")),
                ssl=(ssl if ssl is not None else os.getenv("IMAP_SSL", "true").lower() == "true"),
                user=user or os.getenv("IMAP_USER"),
                password=password or os.getenv("IMAP_PASSWORD"),
                folder=folder,
                max_items=max_,
                allow_senders=self_senders,
                mark_seen=True,
            )
            diagnostic_self = [
                {"vs": vs, "amount": float(amount), "sender": sender}
                for (vs, amount, sender) in self_rows
            ]
        except Exception:
            diagnostic_self = []

        return jsonify({
            "ok": True,
            "shipping_fee_czk": float(fee),
            "matched": processed,
            "unmatched": unmatched,
            "diagnostic_self": diagnostic_self
        }), 200

    except Exception as e:
        current_app.logger.exception("sync_csob_mail failed")
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
