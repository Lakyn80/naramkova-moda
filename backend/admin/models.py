# 📁 backend/admin/models.py

from datetime import datetime
from backend.extensions import db  # ✅ Správný import databázového objektu

# ✅ Kategorie produktů
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Název kategorie
    description = db.Column(db.Text, nullable=True)   # Popis (volitelný)
    group = db.Column(db.String(100), nullable=True)  # Např. "Rodina", "Dárky", "Svatba"

    products = db.relationship("Product", backref="category", lazy=True)  # Vztah s produkty

    def __repr__(self) -> str:
        return f"<Category {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "group": self.group
        }


# ✅ Produkty v e-shopu
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)               # Název produktu
    description = db.Column(db.Text, nullable=True)                # Popis
    price_czk = db.Column(db.Numeric(10, 2), nullable=False)       # Cena v Kč
    image = db.Column(db.String(255), nullable=True)               # Náhledový obrázek
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Datum vytvoření
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Poslední úprava

    media = db.relationship(
        "ProductMedia",
        backref="product",
        lazy=True,
        cascade="all, delete"
    )  # Vztah na víc obrázků/videí

    def __repr__(self) -> str:
        return f"<Product {self.name}>"


# ✅ Média k produktům – obrázky nebo videa
class ProductMedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)     # Jméno souboru
    media_type = db.Column(db.String(20), nullable=False)    # "image" nebo "video"
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)

    def __repr__(self) -> str:
        return f"<ProductMedia {self.media_type} - {self.filename}>"


# ✅ Objednávka – základní údaje o zákazníkovi
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete")

    def __repr__(self):
        return f"<Order #{self.id} – {self.customer_name}>"


# ✅ Položka v objednávce – název, množství a cena
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)


# ✅ Prodaný produkt – archiv historie pro reporty a faktury
class SoldProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_product_id = db.Column(db.Integer)                    # ID původního produktu (pro referenci)
    name = db.Column(db.String(100), nullable=False)               # Název produktu
    description = db.Column(db.Text, nullable=True)                # Popis produktu
    image = db.Column(db.String(255), nullable=True)               # Náhledový obrázek
    price = db.Column(db.String(20), nullable=False)               # Cena jako string (kvůli přesnému formátu)
    quantity = db.Column(db.Integer, nullable=False)               # Počet kusů
    customer_name = db.Column(db.String(100))                      # Jméno zákazníka
    customer_email = db.Column(db.String(100))                     # E-mail
    customer_address = db.Column(db.Text)                          # Adresa
    note = db.Column(db.Text)                                      # Poznámka
    payment_type = db.Column(db.String(50))                        # Dobírka / karta
    sold_at = db.Column(db.DateTime, default=datetime.utcnow)      # Datum prodeje

    def __repr__(self):
        return f"<SoldProduct {self.name} – {self.customer_name}>"
