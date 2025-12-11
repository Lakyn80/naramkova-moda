from backend.extensions import db


class ProductVariantMedia(db.Model):
    __tablename__ = "product_variant_media"

    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(
        db.Integer, db.ForeignKey("product_variant.id", ondelete="CASCADE"), nullable=False
    )
    filename = db.Column(db.String(255), nullable=False)

    variant = db.relationship("ProductVariant", back_populates="media")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ProductVariantMedia {self.filename}>"
