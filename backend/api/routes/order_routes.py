from flask import Blueprint, request, jsonify, current_app
from decimal import Decimal, InvalidOperation
from backend.extensions import db
from backend.admin.models import Order, OrderItem, Payment
from backend.models import Product
import os

order_bp = Blueprint("order_bp", __name__, url_prefix="/api/orders")


def _to_decimal(val, field: str = "") -> Decimal:
    try:
        return Decimal(str(val))
    except Exception:
        raise InvalidOperation(f"Neplatná hodnota {field or 'čísla'}")


@order_bp.post("")
def create_order():
    try:
        data = request.get_json(force=True) or {}

        vs = str(data.get("vs", "")).strip()
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip()
        address = str(data.get("address", "")).strip()
        note = str(data.get("note", "") or "")

        if not (vs and name and email and address):
            return jsonify({"ok": False, "error": "Chybí povinná pole"}), 400

        if Order.query.filter_by(vs=vs).first():
            return jsonify({"ok": False, "error": "Objednávka s tímto VS už existuje."}), 409

        items_in = data.get("items") or []
        if not isinstance(items_in, list) or not items_in:
            return jsonify({"ok": False, "error": "Chybí položky objednávky"}), 400

        subtotal = Decimal("0.00")
        decremented = []

        for it in items_in:
            pid = int(it.get("id"))
            qty = int(it.get("quantity", 1))
            if qty <= 0:
                return jsonify({"ok": False, "error": f"Neplatné množství pro produkt {pid}"}), 400

            product = Product.query.get(pid)
            if not product:
                return jsonify({"ok": False, "error": f"Produkt {pid} neexistuje"}), 404

            if product.stock < qty:
                return jsonify({"ok": False, "error": f"Na skladě zbývá jen {product.stock} ks pro {product.name}"}), 400

            # odečet atomicky přes UPDATE ... WHERE stock >= qty
            updated = db.session.execute(
                db.text(
                    "UPDATE product SET stock = stock - :qty WHERE id = :pid AND stock >= :qty"
                ),
                {"qty": qty, "pid": pid},
            )
            if updated.rowcount == 0:
                return jsonify({"ok": False, "error": f"Nedostatek zásob pro {product.name}"}), 400

            product = Product.query.get(pid)
            decremented.append({
                "id": pid,
                "taken_qty": qty,
                "remaining_stock": product.stock,
            })

            subtotal += (Decimal(str(it.get("price"))) * qty)

        fee_raw = os.getenv("SHIPPING_FEE_CZK") or current_app.config.get("SHIPPING_FEE_CZK", "89.00")
        try:
            shipping_fee = _to_decimal(fee_raw, "shipping_fee")
        except InvalidOperation:
            shipping_fee = Decimal("89.00")

        total_czk = (subtotal + shipping_fee).quantize(Decimal("0.01"))

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
        db.session.flush()

        for it in items_in:
            db.session.add(OrderItem(
                order_id=order.id,
                product_name=it.get("name"),
                quantity=int(it.get("quantity", 1)),
                price=_to_decimal(it.get("price"), "price"),
            ))

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
        current_app.logger.exception("create_order failed")
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
