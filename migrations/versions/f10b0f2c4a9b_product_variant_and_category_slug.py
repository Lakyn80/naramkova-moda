"""add product_variant table and category.slug

Revision ID: f10b0f2c4a9b
Revises: dff4ca27fc90
Create Date: 2025-12-05
"""

from alembic import op
import sqlalchemy as sa
import re
import unicodedata

# revision identifiers, used by Alembic.
revision = "f10b0f2c4a9b"
down_revision = "dff4ca27fc90"
branch_labels = None
depends_on = None


def _slugify(val: str) -> str:
    raw = (val or "").strip().lower()
    try:
        normalized = unicodedata.normalize("NFKD", raw)
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    except Exception:
        normalized = raw
    cleaned = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return cleaned or "kategorie"


def _make_unique(existing: set[str], base: str) -> str:
    base_safe = base or "kategorie"
    candidate = base_safe
    idx = 1
    while candidate in existing:
        idx += 1
        candidate = f"{base_safe}-{idx}"
    existing.add(candidate)
    return candidate


def upgrade():
    with op.batch_alter_table("category", schema=None) as batch_op:
        batch_op.add_column(sa.Column("slug", sa.String(length=150), nullable=True))

    bind = op.get_bind()
    existing_slugs = set()
    rows = list(bind.execute(sa.text("SELECT id, name, slug FROM category")))
    for row in rows:
        if row.slug:
            existing_slugs.add(row.slug)

    for row in rows:
        base = _slugify(row.name or f"category-{row.id}")
        slug = row.slug or _make_unique(existing_slugs, base)
        bind.execute(
            sa.text("UPDATE category SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": row.id},
        )

    with op.batch_alter_table("category", schema=None) as batch_op:
        batch_op.create_unique_constraint("uq_category_slug", ["slug"])

    op.create_table(
        "product_variant",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("product.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("variant_name", sa.String(length=150), nullable=True),
        sa.Column("wrist_size", sa.String(length=50), nullable=True),
        sa.Column("image", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_table("product_variant")

    with op.batch_alter_table("category", schema=None) as batch_op:
        batch_op.drop_constraint("uq_category_slug", type_="unique")
        batch_op.drop_column("slug")
