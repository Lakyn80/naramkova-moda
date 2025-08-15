# 📁 backend/api/routes/payment_routes.py
import io
import os
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, jsonify, current_app, send_file
import qrcode
from sqlalchemy import func

from backend.extensions import db
from backend.admin.models import Order, Payment

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
                pay.amount_czk = amount
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
                "amountCzk": (float(pay.amount_czk) if pay.amount_czk is not None else None),
                "status": pay.status,
                "reference": pay.reference,
                "received_at": (pay.received_at.isoformat() if getattr(pay, "received_at", None) else None),
            },
            "order": None if not order else {
                "id": order.id,
                "status": order.status,
                "totalCzk": (float(order.total_czk) if order.total_czk is not None else None),
                "created_at": (order.created_at.isoformat() if getattr(order, "created_at", None) else None),
            }
        }), 200

    except Exception as e:
        current_app.logger.exception("get_status_by_vs failed")
        return jsonify({"ok": False, "error": str(e)}), 500
