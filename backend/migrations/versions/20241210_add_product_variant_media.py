"""add product_variant_media table

Revision ID: 20241210_add_product_variant_media
Revises: 20241204_add_product_variant_and_category_slug
Create Date: 2024-12-10
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20241210_add_product_variant_media"
down_revision = "f10b0f2c4a9b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "product_variant_media",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["product_variant.id"],
            name="fk_product_variant_media_variant",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("product_variant_media")
