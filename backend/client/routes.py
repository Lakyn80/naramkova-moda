from flask import Blueprint, request, jsonify
from backend.extensions import db
from backend.admin.models import Product, Order, OrderItem, SoldProduct
from backend.models.payment import Payment
from backend.api.utils.email import send_email
from backend.api.utils.generate_vs import generate_vs  # ✅ zůstává
from datetime import datetime

# ✅ pro rezervaci VS (nikdy neopakovat)
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

client_bp = Blueprint("client_bp", __name__)

# --- VS registry (nikdy neopakovat VS) -------------------------------------
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

@client_bp.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json() or {}

    name = data.get("name")
    email = data.get("email")
    address = data.get("address")
    note = data.get("note", "")
    payment_type = data.get("payment_type", "")
    cart_items = data.get("items", [])

    if not all([name, email, address]) or not cart_items:
        return jsonify({"error": "Chybí povinné údaje"}), 400

    # 🔐 VS – použij to, co poslal FE (QR), jinak vygeneruj
    client_vs_raw = data.get("vs")
    client_vs = _sanitize_vs(client_vs_raw)

    try:
        if client_vs:
            _reserve_exact_vs(client_vs)  # může hodit IntegrityError
            vs = client_vs
        else:
            vs = _reserve_unique_vs()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Objednávka s tímto VS už historicky existuje, zkuste znovu."}), 409

    # vytvoření objednávky
    order = Order(
        customer_name=name,
        customer_email=email,
        customer_address=address,
        note=note,
        status="awaiting_payment",
        created_at=datetime.utcnow(),
        vs=vs,  # ✅ uložit stejný VS
    )
    db.session.add(order)
    db.session.flush()  # získáme ID pro další vazby

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

    # záznam o platbě – stejný VS
    payment = Payment(
        vs=vs,
        amount_czk=total_price,
        status="pending",
        reference=f"Objednávka #{order.id}",
        received_at=None
    )
    db.session.add(payment)
    db.session.commit()

    # e-maily
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
📌 Variabilní symbol: {vs}

S pozdravem,
Tým Náramkové Módy
        """.strip()

        # zákazník
        send_email(
            subject="Vaše objednávka",
            recipients=[email],
            body=email_body
        )

        # ✅ kopie pro obchod (samostatná zpráva – zákazník to neuvidí)
        send_email(
            subject="Kopie: Nová objednávka (zákazníkovi odesláno)",
            recipients=["naramkovamoda@email.cz"],
            body=email_body
        )

    except Exception as e:
        print(f"[CHYBA E-MAILU] {e}")

    return jsonify({
        "message": "Objednávka úspěšně vytvořena.",
        "orderId": order.id,
        "vs": vs
    }), 201
