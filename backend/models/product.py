from datetime import datetime
from backend.extensions import db


class Product(db.Model):
    __tablename__ = 'product'
    __table_args__ = {'extend_existing': True}
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price_czk = db.Column(db.Numeric(10, 2), nullable=False)
    image = db.Column(db.String(255), nullable=True)

    # âś… NovĂ˝ sloupec â€“ poÄŤet kusĹŻ na skladÄ›
    stock = db.Column(db.Integer, nullable=False, default=1)

    # FK na kategorii
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    category = db.relationship("Category", back_populates="products")

    # đź”‘ Vztah na mĂ©dia produktu
    media = db.relationship(
        "ProductMedia",
        backref="product",
        lazy=True,
        cascade="all, delete-orphan",
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @property
    def is_in_stock(self) -> bool:
        """VrĂˇtĂ­ True, pokud je produkt skladem (>0 ks)."""
        return self.stock > 0

    def __repr__(self) -> str:
        return f"<Product {self.name}>"

