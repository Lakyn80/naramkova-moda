from __future__ import annotations
from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from backend.extensions import db
from backend.admin.models import Product, Order, OrderItem, Payment

client_bp = Blueprint("client_bp", __name__)

# --- Pomocné ----------------------------------------------------------------

def _to_decimal(val, field: str = "") -> Decimal:
    try:
        return Decimal(str(val))
    except Exception:
        raise InvalidOperation(f"Neplatná hodnota {field or 'čísla'}")

def _ensure_vs_registry():
    """Vytvoří tabulku vs_registry, pokud neexistuje (PRIMARY KEY vs)."""
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS vs_registry (
            vs TEXT PRIMARY KEY
        )
    """))

def _sanitize_vs(v: str | None) -> str | None:
    """Nech jen číslice, max 10 znaků. Vrátí None, pokud nevznikne nic."""
    if not v:
        return None
    s = "".join(ch for ch in str(v) if ch.isdigit())[:10]
    return s if s else None

def _reserve_exact_vs(vs: str):
    """Atomicky zarezervuje konkrétní VS (vloží do vs_registry)."""
    _ensure_vs_registry()
    db.session.execute(text("INSERT INTO vs_registry (vs) VALUES (:vs)"), {"vs": vs})

def _reserve_unique_vs(max_tries: int = 50) -> str:
    """Vygeneruje a zarezervuje unikátní VS (nikdy nepoužité)."""
    from backend.api.utils.generate_vs import generate_vs  # lokální import, ať necyklíme
    _ensure_vs_registry()
    tries = 0
    while tries < max_tries:
        vs = generate_vs()  # očekává se 10 číslic
        try:
            _reserve_exact_vs(vs)
            return vs
        except IntegrityError:
            db.session.rollback()
            tries += 1
            continue
    raise RuntimeError("Nepodařilo se zarezervovat unikátní VS (zkus znovu).")

# --- API --------------------------------------------------------------------

@client_bp.route("/api/orders/client", methods=["POST"])
def create_order_client():
    """
    Kompatibilní endpoint pro FE (klientské vytvoření objednávky).
    - Sjednocená logika se skladem: ATOMICKÝ odečet přes SQL:
        UPDATE product SET stock = stock - :qty WHERE id=:pid AND stock >= :qty
    - ŽÁDNÉ mazání produktů, ŽÁDNÝ SoldProduct při vytvoření objednávky.
    - VS: použij VS z FE (pokud dorazí a je volný), jinak vygeneruj a zarezervuj.
    Body JSON:
    {
      "vs": "123456",                # volitelné (pokud posílá FE/QR)
      "name": "...", "email": "...", "address": "...",
      "note": "...",
      "items": [
        {"id": 1, "name": "Náramek A", "quantity": 2, "price": 199.0}
      ]
    }
    """
    try:
        data = request.get_json(force=True) or {}

        # --- Povinné údaje zákazníka ---
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip()
        address = str(data.get("address", "")).strip()
        note = str(data.get("note", "") or "")
        if not (name and email and address):
            return jsonify({"ok": False, "error": "Chybí povinná pole (name, email, address)."}), 400

        # --- Položky košíku ---
        items_in = data.get("items") or []
        if not isinstance(items_in, list) or not items_in:
            return jsonify({"ok": False, "error": "Chybí položky objednávky (items)."}), 400

        # --- VS: použij klientský, jinak vygeneruj a zarezervuj ---
        client_vs = _sanitize_vs(data.get("vs"))
        try:
            if client_vs:
                _reserve_exact_vs(client_vs)
                vs = client_vs
            else:
                vs = _reserve_unique_vs()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"ok": False, "error": "Objednávka s tímto VS už existuje, zkuste znovu."}), 409

        # Bez kolize s existující objednávkou:
        if Order.query.filter_by(vs=vs).first():
            return jsonify({"ok": False, "error": "Objednávka s tímto VS už existuje."}), 409

        # --- Výpočet subtotal + poštovné ---
        subtotal = Decimal("0.00")
        for it in items_in:
            qty = int(it.get("quantity", 1))
            price = _to_decimal(it.get("price", "0"), "price")
            if qty <= 0 or price <= 0:
                return jsonify({"ok": False, "error": "Položka musí mít quantity>0 a price>0."}), 400
            subtotal += (price * qty)

        # Poštovné z ENV / config, default 89
        import os
        fee_raw = os.getenv("SHIPPING_FEE_CZK") or current_app.config.get("SHIPPING_FEE_CZK", "89.00")
        try:
            shipping_fee = _to_decimal(fee_raw, "shipping_fee")
        except InvalidOperation:
            shipping_fee = Decimal("89.00")

        total_czk = (subtotal + shipping_fee).quantize(Decimal("0.01"))
        if total_czk <= 0:
            return jsonify({"ok": False, "error": "Částka musí být > 0."}), 400

        # --- ATOMICKÝ ODEČET SKLADU (shodné chování jako v /api/orders) ---
        decremented = []
        for it in items_in:
            pid = int(it.get("id"))
            qty = int(it.get("quantity", 1))

            product = Product.query.get(pid)
            if not product:
                return jsonify({"ok": False, "error": f"Produkt {pid} neexistuje"}), 404

            current_stock = int(product.stock or 0)
            if current_stock < qty:
                return jsonify({"ok": False, "error": f"Na skladě zbývá jen {current_stock} ks pro {product.name}"}), 400

            updated = db.session.execute(
                db.text("UPDATE product SET stock = stock - :qty WHERE id = :pid AND stock >= :qty"),
                {"qty": qty, "pid": pid},
            )
            if updated.rowcount == 0:
                latest = Product.query.get(pid)
                left = int(latest.stock or 0) if latest else 0
                return jsonify({"ok": False, "error": f"Na skladě zbývá jen {left} ks pro {product.name}"}), 400

            latest = Product.query.get(pid)
            decremented.append({
                "id": pid,
                "taken_qty": qty,
                "remaining_stock": int(latest.stock or 0) if latest else 0,
            })

        # --- Vytvoření Order + položek ---
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
