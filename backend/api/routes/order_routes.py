from flask import Blueprint, request, jsonify, current_app
from decimal import Decimal, InvalidOperation
from backend.extensions import db, mail
from backend.admin.models import Order, OrderItem, Payment
from backend.models import Product  # kvůli skladu
from flask_mail import Message
import os

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
      "items": [
        {"id": 1, "name": "Náramek A", "quantity": 2, "price": 199.0}
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
            subtotal += (price * qty)

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

        existing_p = Payment.query.filter_by(vs=vs).first()
        if not existing_p:
            db.session.add(Payment(
                vs=vs,
                amount_czk=total_czk,
                status="pending",
                reference=f"Order #{order.id} created"
            ))

        db.session.commit()

        # --- NOVĚ: potvrzovací e-mail zákazníkovi (nic jiného se nemění) ---
        try:
            subject = "Potvrzení objednávky – Náramková Móda"
            lines = []
            lines.append(f"Dobrý den {name},")
            lines.append("")
            lines.append("děkujeme za Vaši objednávku. Níže je její rekapitulace:")
            lines.append(f"- VS: {vs}")
            lines.append(f"- Dodací adresa: {address}")
            if note:
                lines.append(f"- Poznámka: {note}")
            lines.append("")
            lines.append("Položky:")
            for it in items_in:
                nm = str(it.get("name") or "").strip()
                qty = int(it.get("quantity", 1))
                price = _to_decimal(it.get("price", "0"), "price")
                lines.append(f"  • {nm} × {qty} – {price:.2f} Kč/ks")
            lines.append("")
            lines.append(f"Poštovné: {shipping_fee:.2f} Kč")
            lines.append(f"Celkem k úhradě: {total_czk:.2f} Kč")
            lines.append("")
            lines.append("Pokyny k platbě:")
            lines.append("— Bankovní převod v CZK")
            iban = (os.getenv("MERCHANT_IBAN") or current_app.config.get("MERCHANT_IBAN") or "").replace(" ", "")
            if iban:
                lines.append(f"— IBAN: {iban}")
            lines.append(f"— Variabilní symbol: {vs}")
            lines.append("")
            lines.append("Po připsání platby Vám automaticky zašleme fakturu v PDF a nákup se zobrazí v sekci Prodané.")
            lines.append("")
            lines.append("Děkujeme za nákup.")
            lines.append("Náramková Móda")

            msg = Message(subject=subject, recipients=[email], body="\n".join(lines))
            mail.send(msg)
        except Exception:
            # nechceme ohrozit vytvoření objednávky, případné chyby jen zalogujeme
            current_app.logger.exception("Potvrzovací e-mail po create_order selhal")

        # --- NOVĚ: notifikace majiteli o nové objednávce ---
        try:
            owner_rcpt = (
                current_app.config.get("ORDER_NOTIFY_EMAIL")
                or os.getenv("ORDER_NOTIFY_EMAIL")
                or current_app.config.get("MAIL_DEFAULT_SENDER")
                or os.getenv("MAIL_DEFAULT_SENDER")
            )
            if owner_rcpt:
                subject_owner = f"Nová objednávka #{order.id} (VS {vs})"
                items_lines = []
                for it in items_in:
                    q = int(it.get("quantity", 1))
                    p = _to_decimal(it.get("price", "0"), "price")
                    items_lines.append(f"- {str(it.get('name','?')).strip()} × {q} @ {float(p):.2f} Kč")
                body_owner = (
                    f"Nová objednávka #{order.id}\n"
                    f"VS: {vs}\n"
                    f"Zákazník: {name} <{email}>\n"
                    f"Adresa: {address}\n"
                    f"Poznámka: {note or '-'}\n\n"
                    f"Položky:\n" + "\n".join(items_lines) + "\n\n"
                    f"Poštovné: {float(shipping_fee):.2f} Kč\n"
                    f"Celkem: {float(total_czk):.2f} Kč\n"
                )
                msg_owner = Message(subject=subject_owner, recipients=[owner_rcpt], body=body_owner)
                mail.send(msg_owner)
            else:
                current_app.logger.warning("ORDER_NOTIFY_EMAIL/MAIL_DEFAULT_SENDER not set; owner notification skipped")
        except Exception:
            current_app.logger.exception("Order email to owner failed")

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

