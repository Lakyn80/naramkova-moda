from datetime import datetime
from backend.extensions import db

class Product(db.Model):
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price_czk = db.Column(db.Numeric(10, 2), nullable=False)
    image = db.Column(db.String(255), nullable=True)

    # FK na kategorii
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    category = db.relationship("Category", back_populates="products")

    # 🔑 DŮLEŽITÉ: vztah na média produktu (aby šablony i API měly data)
    media = db.relationship(
        "ProductMedia",
        backref="product",
        lazy=True,
        cascade="all, delete-orphan",
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Product {self.name}>"
