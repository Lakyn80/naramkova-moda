from backend.extensions import db
from backend.models.product import Product
from backend.models.product_variant_media import ProductVariantMedia


class ProductVariant(db.Model):
    __tablename__ = "product_variant"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("product.id", ondelete="CASCADE"), nullable=False
    )
    variant_name = db.Column(db.String(150), nullable=True)
    wrist_size = db.Column(db.String(50), nullable=True)
    image = db.Column(db.String(255), nullable=True)

    product = db.relationship(Product, back_populates="variants")
    media = db.relationship(
        ProductVariantMedia,
        back_populates="variant",
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<ProductVariant {self.variant_name or ''} ({self.wrist_size or ''})>"
