# backend/client/routes.py

from flask import Blueprint, request, jsonify
from backend.extensions import db
from backend.admin.models import Product, Order, OrderItem, SoldProduct
from backend.models.payment import Payment   # ✅ důležitý import
from backend.api.utils.email import send_email
from datetime import datetime

client_bp = Blueprint("client_bp", __name__)

@client_bp.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    address = data.get("address")
    note = data.get("note", "")
    payment_type = data.get("payment_type", "")
    cart_items = data.get("items", [])

    if not all([name, email, address]) or not cart_items:
        return jsonify({"error": "Chybí povinné údaje"}), 400

    # vytvoření objednávky
    order = Order(
        customer_name=name,
        customer_email=email,
        customer_address=address,
        note=note,
        status="awaiting_payment",   # ✅ čeká na platbu
        created_at=datetime.utcnow()
    )
    db.session.add(order)
    db.session.flush()  # získáme ID (pro VS)

    total_price = 0

    for item in cart_items:
        product_name = item.get("name")
        quantity = item.get("quantity", 1)

        product = Product.query.filter_by(name=product_name).first()
        if product:
            total_price += float(product.price_czk) * quantity

            order_item = OrderItem(
                product_name=product.name,
                quantity=quantity,
                price=product.price_czk,
                order=order
            )
            db.session.add(order_item)

            sold = SoldProduct(
                original_product_id=product.id,
                name=product.name,
                description=product.description,
                image=product.image,
                price=str(product.price_czk),
                quantity=quantity,
                customer_name=name,
                customer_email=email,
                customer_address=address,
                note=note,
                payment_type=payment_type,
                sold_at=datetime.utcnow()
            )
            db.session.add(sold)

            db.session.delete(product)

    # vytvoření Payment záznamu
    payment = Payment(
        vs=str(order.id),
        amount_czk=total_price,
        status="pending",   # ✅ čeká na přijetí
        reference=f"Objednávka #{order.id}",
        received_at=None    # dokud není zaplaceno
    )
    db.session.add(payment)

    db.session.commit()

    # odeslání e-mailu
    try:
        product_list = "\n".join([
            f"- {item['quantity']}× {item['name']} za {item['price']} Kč"
            for item in cart_items
        ])
        email_body = f"""
Dobrý den, {name}!

Děkujeme za Vaši objednávku. Níže jsou detaily:

📍 Adresa:
{address}

📝 Poznámka:
{note or '—'}

🛒 Položky:
{product_list}

💰 Celková cena: {total_price:.2f} Kč
📌 Variabilní symbol: {order.id}

S pozdravem,
Tým Náramkové Módy
        """.strip()

        send_email(
            subject="Vaše objednávka",
            recipients=[email],
            body=email_body
        )
    except Exception as e:
        print(f"[CHYBA E-MAILU] {e}")

    return jsonify({"message": "Objednávka úspěšně vytvořena.", "orderId": order.id, "vs": str(order.id)}), 201
