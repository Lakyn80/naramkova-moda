from flask import Blueprint, request, jsonify, current_app
from decimal import Decimal, InvalidOperation
from backend.extensions import db
from backend.models import Order, OrderItem, Payment, Product
from backend.api.utils.email import send_email
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
            return jsonify({"ok": False, "error": "Chybí povinná pole (vs, name, email, address)."}), 400

        if Order.query.filter_by(vs=vs).first():
            return jsonify({"ok": False, "error": "Objednávka s tímto VS už existuje."}), 409

        items_in = data.get("items") or []
        if not isinstance(items_in, list) or not items_in:
            return jsonify({"ok": False, "error": "Chybí položky objednávky (items)."}), 400

        subtotal = Decimal("0.00")
        for it in items_in:
            qty = int(it.get("quantity", 1))
            price = _to_decimal(it.get("price", "0"), "price")
            if qty <= 0 or price <= 0:
                return jsonify({"ok": False, "error": "Položka musí mít quantity>0 a price>0."}), 400
            subtotal += price * qty

        fee_raw = os.getenv("SHIPPING_FEE_CZK") or current_app.config.get("SHIPPING_FEE_CZK", "89.00")
        try:
            shipping_fee = _to_decimal(fee_raw, "shipping_fee")
        except InvalidOperation:
            shipping_fee = Decimal("89.00")

        total_czk = (subtotal + shipping_fee).quantize(Decimal("0.01"))
        if total_czk <= 0:
            return jsonify({"ok": False, "error": "Částka musí být > 0."}), 400

        # --- ATOMICKÝ ODEČET SKLADU ---
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
                product_name=str(it.get("name") or "").strip(),
                quantity=int(it.get("quantity", 1)),
                price=_to_decimal(it.get("price"), "price"),
            ))

        if not Payment.query.filter_by(vs=vs).first():
            db.session.add(Payment(
                vs=vs,
                amount_czk=total_czk,
                status="pending",
                reference=f"Objednávka #{order.id}"
            ))

        db.session.commit()

        # =========================
        # POTVRZOVACÍ E-MAIL ZÁKAZNÍK
        # =========================
        try:
            lines = [
                f"Dobrý den {name},",
                "",
                "děkujeme za Vaši objednávku. Níže je její rekapitulace:",
                f"VS: {vs}",
                f"Dodací adresa: {address}",
            ]
            if note:
                lines.append(f"Poznámka: {note}")

            lines.append("")
            lines.append("Položky:")
            for it in items_in:
                nm = str(it.get("name") or "").strip()
                qty = int(it.get("quantity", 1))
                price = _to_decimal(it.get("price", "0"), "price")
                lines.append(f"• {nm} × {qty} – {price:.2f} Kč/ks")

            lines += [
                "",
                f"Poštovné: {shipping_fee:.2f} Kč",
                f"Celkem k úhradě: {total_czk:.2f} Kč",
                "",
                "Pokyny k platbě:",
                "— Bankovní převod v CZK",
                f"— Variabilní symbol: {vs}",
                "",
                "Po připsání platby Vám automaticky zašleme fakturu v PDF.",
                "",
                "Děkujeme za nákup.",
                "Náramková Móda",
            ]

            send_email(
                subject="Potvrzení objednávky – Náramková Móda",
                recipients=[email],
                body="\n".join(lines),
            )
        except Exception:
            current_app.logger.exception("Potvrzovací e-mail selhal")

        # =========================
        # NOTIFIKACE MAJITELI
        # =========================
        try:
            owner = (
                current_app.config.get("ORDER_NOTIFY_EMAIL")
                or os.getenv("ORDER_NOTIFY_EMAIL")
            )
            if owner:
                send_email(
                    subject=f"Nová objednávka #{order.id} (VS {vs})",
                    recipients=[owner],
                    body=(
                        f"Objednávka #{order.id}\n"
                        f"VS: {vs}\n"
                        f"Zákazník: {name} <{email}>\n"
                        f"Adresa: {address}\n"
                        f"Celkem: {total_czk:.2f} Kč"
                    ),
                )
        except Exception:
            current_app.logger.exception("Owner e-mail selhal")

        return jsonify({
            "ok": True,
            "orderId": order.id,
            "vs": vs,
            "status": order.status,
            "decremented_items": decremented,
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("create_order failed")
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
