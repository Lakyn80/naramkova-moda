# 📁 backend/api/routes/payment_routes.py
import io
import os
from decimal import Decimal, InvalidOperation
from flask import Blueprint, request, jsonify, current_app, send_file
import qrcode

payment_bp = Blueprint("payment_bp", __name__, url_prefix="/api/payments")

def _get_iban():
    """
    IBAN obchodníka pro QR platbu.
    Vezme z ENV MERCHANT_IBAN nebo z Flask configu Config.MERCHANT_IBAN.
    """
    iban = os.getenv("MERCHANT_IBAN") or current_app.config.get("MERCHANT_IBAN")
    if not iban:
        raise RuntimeError("MERCHANT_IBAN není nastaven (ENV nebo Config).")
    return iban.replace(" ", "").upper()

def _build_spd_payload(iban: str, amount: Decimal, vs: str | None, msg: str | None) -> str:
    """
    Vytvoří SPD 1.0 payload pro české QR platby (CZK).
    Viz https://qr-platba.cz (SPD*1.0*ACC:...*AM:...*CC:CZK*X-VS:...*MSG:...)
    """
    parts = ["SPD*1.0", f"ACC:{iban}", f"AM:{amount:.2f}", "CC:CZK"]
    if vs:
        parts.append(f"X-VS:{vs}")
    if msg:
        # SPD standard povoluje ASCII; pro jednoduchost vynecháme diakritiku/emoji.
        safe_msg = "".join(ch for ch in msg if 32 <= ord(ch) <= 126)
        parts.append(f"MSG:{safe_msg[:60]}")  # zprávu zkrátíme (typické limity čteček)
    return "*".join(parts)

@payment_bp.get("/qr")
def payment_qr_png():
    """
    GET /api/payments/qr?amount=1234.00&vs=20250814&msg=Objednavka%20123
    Vrací PNG s QR kódem (MIME image/png).
    """
    try:
        amount_raw = request.args.get("amount", "").strip()
        if not amount_raw:
            return jsonify({"ok": False, "error": "Chybí query param 'amount'."}), 400
        try:
            amount = Decimal(amount_raw)
        except InvalidOperation:
            return jsonify({"ok": False, "error": "Neplatná částka 'amount'."}), 400
        if amount <= 0:
            return jsonify({"ok": False, "error": "Částka musí být > 0."}), 400

        vs = request.args.get("vs", "").strip() or None
        msg = request.args.get("msg", "").strip() or None

        iban = _get_iban()
        payload = _build_spd_payload(iban, amount, vs, msg)

        # QR kód jako PNG do paměti
        img = qrcode.make(payload)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        # Cache-control nízko, aby se u dynamických částek negenerovala dlouhá cache
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
    """
    Volitelný helper:
    GET /api/payments/qr/payload?amount=...&vs=...&msg=...
    Vrátí JSON s SPD payloadem (pro debug nebo generování QR na frontendu).
    """
    try:
        amount_raw = request.args.get("amount", "").strip()
        if not amount_raw:
            return jsonify({"ok": False, "error": "Chybí query param 'amount'."}), 400
        try:
            amount = Decimal(amount_raw)
        except InvalidOperation:
            return jsonify({"ok": False, "error": "Neplatná částka 'amount'."}), 400
        if amount <= 0:
            return jsonify({"ok": False, "error": "Částka musí být > 0."}), 400

        vs = request.args.get("vs", "").strip() or None
        msg = request.args.get("msg", "").strip() or None

        iban = _get_iban()
        payload = _build_spd_payload(iban, amount, vs, msg)
        return jsonify({"ok": True, "iban": iban, "payload": payload})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
