from datetime import datetime
from extensions import db

# ─── Category model ───────────────────────────────────────────────
class Category(db.Model):
    """
    Reprezentuje kategorii produktů.
    """
    id = db.Column(db.Integer, primary_key=True)  
    name = db.Column(db.String(100), nullable=False)  
    description = db.Column(db.Text, nullable=True)  
    
    # Vztah 1:N – jedna kategorie může mít mnoho produktů
    products = db.relationship("Product", backref="category", lazy=True)

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


# ─── Product model ────────────────────────────────────────────────
class Product(db.Model):
    """
    Reprezentuje produkt v e-shopu, s hlavním obrázkem a
    volitelnou kategorií. Přidružená média v media[].
    """
    id = db.Column(db.Integer, primary_key=True)  
    name = db.Column(db.String(150), nullable=False, unique=True)  
    description = db.Column(db.Text, nullable=True)  
    price_czk = db.Column(db.Numeric(10, 2), nullable=False)  
    
    # Hlavní obrázek – udržuje jméno uloženého souboru
    image = db.Column(db.String(255), nullable=True)  
    
    # Volitelná kategorie (cizí klíč)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)  
    
    # Čas vytvoření a poslední aktualizace
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  

    # Vztah 1:N k médiím – obrázky ↔ videa
    media = db.relationship(
        "ProductMedia",
        backref="product",
        lazy=True,
        cascade="all, delete"
    )

    def __repr__(self) -> str:
        return f"<Product {self.name}>"


# ─── ProductMedia model ──────────────────────────────────────────
class ProductMedia(db.Model):
    """
    Reprezentuje jeden soubor (obrázek nebo video) přidružený
    k produktu. Ukládá jméno souboru a typ media_type.
    """
    id = db.Column(db.Integer, primary_key=True)  
    filename = db.Column(db.String(255), nullable=False)  
    media_type = db.Column(db.String(20), nullable=False)  # "image" nebo "video"
    
    # Cizí klíč na Product.id
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)  

    def __repr__(self) -> str:
        return f"<ProductMedia {self.media_type} - {self.filename}>"
