# backend/models/product_media.py
from backend.extensions import db

class ProductMedia(db.Model):
    __tablename__ = 'productmedia'
    __table_args__ = {'extend_existing': True}
    __tablename__ = "product_media"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)  # "image" | "video"
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)

    def __repr__(self) -> str:
        return f"<ProductMedia {self.media_type} - {self.filename}>"

