from __future__ import annotations
from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from backend.extensions import db
from backend.models import Product, Order, OrderItem, Payment

client_bp = Blueprint("client_bp", __name__)

# --- PomocnĂ© ----------------------------------------------------------------

def _to_decimal(val, field: str = "") -> Decimal:
    try:
        return Decimal(str(val))
    except Exception:
        raise InvalidOperation(f"NeplatnĂˇ hodnota {field or 'ÄŤĂ­sla'}")

def _ensure_vs_registry():
    """VytvoĹ™Ă­ tabulku vs_registry, pokud neexistuje (PRIMARY KEY vs)."""
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS vs_registry (
            vs TEXT PRIMARY KEY
        )
    """))

def _sanitize_vs(v: str | None) -> str | None:
    """Nech jen ÄŤĂ­slice, max 10 znakĹŻ. VrĂˇtĂ­ None, pokud nevznikne nic."""
    if not v:
        return None
    s = "".join(ch for ch in str(v) if ch.isdigit())[:10]
    return s if s else None

def _reserve_exact_vs(vs: str):
    """Atomicky zarezervuje konkrĂ©tnĂ­ VS (vloĹľĂ­ do vs_registry)."""
    _ensure_vs_registry()
    db.session.execute(text("INSERT INTO vs_registry (vs) VALUES (:vs)"), {"vs": vs})

def _reserve_unique_vs(max_tries: int = 50) -> str:
    """Vygeneruje a zarezervuje unikĂˇtnĂ­ VS (nikdy nepouĹľitĂ©)."""
    from backend.api.utils.generate_vs import generate_vs  # lokĂˇlnĂ­ import, aĹĄ necyklĂ­me
    _ensure_vs_registry()
    tries = 0
    while tries < max_tries:
        vs = generate_vs()  # oÄŤekĂˇvĂˇ se 10 ÄŤĂ­slic
        try:
            _reserve_exact_vs(vs)
            return vs
        except IntegrityError:
            db.session.rollback()
            tries += 1
            continue
    raise RuntimeError("NepodaĹ™ilo se zarezervovat unikĂˇtnĂ­ VS (zkus znovu).")

# --- API --------------------------------------------------------------------

@client_bp.route("/api/orders/client", methods=["POST"])
def create_order_client():
    """
    KompatibilnĂ­ endpoint pro FE (klientskĂ© vytvoĹ™enĂ­ objednĂˇvky).
    - SjednocenĂˇ logika se skladem: ATOMICKĂť odeÄŤet pĹ™es SQL:
        UPDATE product SET stock = stock - :qty WHERE id=:pid AND stock >= :qty
    - Ĺ˝ĂDNĂ‰ mazĂˇnĂ­ produktĹŻ, Ĺ˝ĂDNĂť SoldProduct pĹ™i vytvoĹ™enĂ­ objednĂˇvky.
    - VS: pouĹľij VS z FE (pokud dorazĂ­ a je volnĂ˝), jinak vygeneruj a zarezervuj.
    Body JSON:
    {
      "vs": "123456",                # volitelnĂ© (pokud posĂ­lĂˇ FE/QR)
      "name": "...", "email": "...", "address": "...",
      "note": "...",
      "items": [
        {"id": 1, "name": "NĂˇramek A", "quantity": 2, "price": 199.0}
      ]
    }
    """
    try:
        data = request.get_json(force=True) or {}

        # --- PovinnĂ© Ăşdaje zĂˇkaznĂ­ka ---
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip()
        address = str(data.get("address", "")).strip()
        note = str(data.get("note", "") or "")
        if not (name and email and address):
            return jsonify({"ok": False, "error": "ChybĂ­ povinnĂˇ pole (name, email, address)."}), 400

        # --- PoloĹľky koĹˇĂ­ku ---
        items_in = data.get("items") or []
        if not isinstance(items_in, list) or not items_in:
            return jsonify({"ok": False, "error": "ChybĂ­ poloĹľky objednĂˇvky (items)."}), 400

        # --- VS: pouĹľij klientskĂ˝, jinak vygeneruj a zarezervuj ---
        client_vs = _sanitize_vs(data.get("vs"))
        try:
            if client_vs:
                _reserve_exact_vs(client_vs)
                vs = client_vs
            else:
                vs = _reserve_unique_vs()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"ok": False, "error": "ObjednĂˇvka s tĂ­mto VS uĹľ existuje, zkuste znovu."}), 409

        # Bez kolize s existujĂ­cĂ­ objednĂˇvkou:
        if Order.query.filter_by(vs=vs).first():
            return jsonify({"ok": False, "error": "ObjednĂˇvka s tĂ­mto VS uĹľ existuje."}), 409

        # --- VĂ˝poÄŤet subtotal + poĹˇtovnĂ© ---
        subtotal = Decimal("0.00")
        for it in items_in:
            qty = int(it.get("quantity", 1))
            price = _to_decimal(it.get("price", "0"), "price")
            if qty <= 0 or price <= 0:
                return jsonify({"ok": False, "error": "PoloĹľka musĂ­ mĂ­t quantity>0 a price>0."}), 400
            subtotal += (price * qty)

        # PoĹˇtovnĂ© z ENV / config, default 89
        import os
        fee_raw = os.getenv("SHIPPING_FEE_CZK") or current_app.config.get("SHIPPING_FEE_CZK", "89.00")
        try:
            shipping_fee = _to_decimal(fee_raw, "shipping_fee")
        except InvalidOperation:
            shipping_fee = Decimal("89.00")

        total_czk = (subtotal + shipping_fee).quantize(Decimal("0.01"))
        if total_czk <= 0:
            return jsonify({"ok": False, "error": "ÄŚĂˇstka musĂ­ bĂ˝t > 0."}), 400

        # --- ATOMICKĂť ODEÄŚET SKLADU (shodnĂ© chovĂˇnĂ­ jako v /api/orders) ---
        decremented = []
        for it in items_in:
            pid = int(it.get("id"))
            qty = int(it.get("quantity", 1))

            product = Product.query.get(pid)
            if not product:
                return jsonify({"ok": False, "error": f"Produkt {pid} neexistuje"}), 404

            current_stock = int(product.stock or 0)
            if current_stock < qty:
                return jsonify({"ok": False, "error": f"Na skladÄ› zbĂ˝vĂˇ jen {current_stock} ks pro {product.name}"}), 400

            updated = db.session.execute(
                db.text("UPDATE product SET stock = stock - :qty WHERE id = :pid AND stock >= :qty"),
                {"qty": qty, "pid": pid},
            )
            if updated.rowcount == 0:
                latest = Product.query.get(pid)
                left = int(latest.stock or 0) if latest else 0
                return jsonify({"ok": False, "error": f"Na skladÄ› zbĂ˝vĂˇ jen {left} ks pro {product.name}"}), 400

            latest = Product.query.get(pid)
            decremented.append({
                "id": pid,
                "taken_qty": qty,
                "remaining_stock": int(latest.stock or 0) if latest else 0,
            })

        # --- VytvoĹ™enĂ­ Order + poloĹľek ---
        order = Order(
            vs=vs,
            customer_name=name,
            customer_email=email,
            customer_address=address,
            note=note,
            total_czk=total_czk,
            status="awaiting_payment",
            created_at=datetime.utcnow(),
        )
        db.session.add(order)
        db.session.flush()

        for it in items_in:
            db.session.add(OrderItem(
                order_id=order.id,
                product_name=str(it.get("name") or "").strip(),
                quantity=int(it.get("quantity", 1)),
                price=_to_decimal(it.get("price"), "price"),
            ))

        # --- Payment pending (pokud neexistuje) ---
        existing_p = Payment.query.filter_by(vs=vs).first()
        if not existing_p:
            db.session.add(Payment(
                vs=vs,
                amount_czk=total_czk,
                status="pending",
                reference=f"Order #{order.id} created"
            ))

        db.session.commit()

        return jsonify({
            "ok": True,
            "orderId": order.id,
            "vs": vs,
            "status": order.status,
            "decremented_items": decremented,
        }), 201

    except Exception as e:
        current_app.logger.exception("create_order_client failed")
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

