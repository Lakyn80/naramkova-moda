"""Sync Product.name without unique constraint

Revision ID: 29044e73de5e
Revises: 0300051c3906
Create Date: 2025-07-16 00:25:29.889565
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '29044e73de5e'
down_revision = '0300051c3906'
branch_labels = None
depends_on = None


def upgrade():
    # ✅ Bezpečně přidáme pojmenovaný cizí klíč (aby neházel chybu)
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_product_category",        # ✅ název constraintu
            "category",                   # tabulka, na kterou se váže
            ["category_id"],              # sloupec v product
            ["id"]                        # sloupec v category
        )


def downgrade():
    # ✅ Dropneme pojmenovaný foreign key (pro rollback)
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_product_category",        # ✅ název musí sedět
            type_="foreignkey"
        )
