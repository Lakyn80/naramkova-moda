# 📁 backend/api/routes/order_routes.py
from flask import Blueprint, request, jsonify, current_app
from decimal import Decimal, InvalidOperation
from backend.extensions import db
from backend.admin.models import Order, OrderItem, Payment  # ← přidán Payment

order_bp = Blueprint("order_bp", __name__, url_prefix="/api/orders")


def _to_decimal(val, field: str = "") -> Decimal:
    try:
        return Decimal(str(val))
    except Exception:
        raise InvalidOperation(f"Neplatná hodnota {field or 'čísla'}")


@order_bp.post("")
def create_order():
    """
    Body (JSON):
    {
      "vs": "123456",
      "name": "...",
      "email": "...",
      "address": "...",
      "note": "...",
      "totalCzk": 1234.00,
      "items": [
        {"id": 1, "name": "Náramek A", "quantity": 2, "price": 199.0},
        ...
      ]
    }
    """
    try:
        data = request.get_json(force=True) or {}

        vs = str(data.get("vs", "")).strip()
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip()
        address = str(data.get("address", "")).strip()
        note = str(data.get("note", "") or "")

        if not (vs and name and email and address):
            return jsonify({"ok": False, "error": "Chybí povinná pole (vs, name, email, address)."}), 400

        # VS unikátní na objednávku (aplikační kontrola)
        if Order.query.filter_by(vs=vs).first():
            return jsonify({"ok": False, "error": "Objednávka s tímto VS už existuje."}), 409

        try:
            total_czk = _to_decimal(data.get("totalCzk", "0"), "totalCzk")
            if total_czk <= 0:
                raise InvalidOperation("Částka musí být > 0")
        except InvalidOperation:
            return jsonify({"ok": False, "error": "Neplatná částka totalCzk."}), 400

        items_in = data.get("items") or []
        if not isinstance(items_in, list) or not items_in:
            return jsonify({"ok": False, "error": "Chybí položky objednávky (items)."}), 400

        # Vytvořit objednávku
        order = Order(
            vs=vs,
            customer_name=name,
            customer_email=email,
            customer_address=address,
            note=note,
            total_czk=total_czk,
            status="awaiting_payment",
        )
        db.session.add(order)
        db.session.flush()  # získáme order.id

        # Položky
        for it in items_in:
            try:
                pname = str(it.get("name") or "").strip()
                qty = int(it.get("quantity", 1))
                price = _to_decimal(it.get("price", "0"), "price")
            except Exception:
                db.session.rollback()
                return jsonify({"ok": False, "error": "Neplatná položka (name/quantity/price)."}), 400

            if not pname or qty <= 0 or price <= 0:
                db.session.rollback()
                return jsonify({"ok": False, "error": "Položka musí mít name, quantity>0 a price>0."}), 400

            db.session.add(OrderItem(
                order_id=order.id,
                product_name=pname,
                quantity=qty,
                price=price,
            ))

        # 💳 Založ (pokud neexistuje) záznam v payments – pending, aby byl hned vidět v adminu
        existing_p = Payment.query.filter_by(vs=vs).first()
        if not existing_p:
            db.session.add(Payment(
                vs=vs,
                amount_czk=total_czk,
                status="pending",
                reference=f"Order #{order.id} created"
            ))

        db.session.commit()
        return jsonify({"ok": True, "orderId": order.id, "vs": vs, "status": order.status}), 201

    except Exception as e:
        current_app.logger.exception("create_order failed")
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@order_bp.get("/<int:order_id>")
def get_order(order_id: int):
    o = Order.query.get_or_404(order_id)
    return jsonify({
        "ok": True,
        "order": {
            "id": o.id,
            "vs": o.vs,
            "name": o.customer_name,
            "email": o.customer_email,
            "address": o.customer_address,
            "note": o.note,
            "totalCzk": float(o.total_czk) if o.total_czk is not None else None,
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "items": [
                {
                    "id": it.id,
                    "name": it.product_name,
                    "quantity": it.quantity,
                    "price": float(it.price),
                    "subtotal": float(it.price) * it.quantity,
                } for it in o.items
            ]
        }
    }), 200


@order_bp.get("/by-vs/<vs>")
def get_order_by_vs(vs: str):
    o = Order.query.filter_by(vs=str(vs).strip()).first()
    if not o:
        return jsonify({"ok": False, "error": "Objednávka s tímto VS neexistuje."}), 404
    return jsonify({
        "ok": True,
        "order": {
            "id": o.id,
            "vs": o.vs,
            "name": o.customer_name,
            "email": o.customer_email,
            "address": o.customer_address,
            "note": o.note,
            "totalCzk": float(o.total_czk) if o.total_czk is not None else None,
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "items": [
                {
                    "id": it.id,
                    "name": it.product_name,
                    "quantity": it.quantity,
                    "price": float(it.price),
                    "subtotal": float(it.price) * it.quantity,
                } for it in o.items
            ]
        }
    }), 200
