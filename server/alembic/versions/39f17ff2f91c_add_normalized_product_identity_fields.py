"""add normalized product identity fields

Revision ID: 39f17ff2f91c
Revises: fcf86696d73c
Create Date: 2026-03-24 15:04:06.773982
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

revision: str = "39f17ff2f91c"
down_revision: Union[str, None] = "fcf86696d73c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _normalize(value: str | None) -> str | None:
    import re
    import unicodedata

    if value is None:
        return None

    value = value.strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"\s+", " ", value)
    return value


def upgrade() -> None:
    op.add_column("products", sa.Column("name_normalized", sa.String(length=255), nullable=True))
    op.add_column("products", sa.Column("brand_normalized", sa.String(length=100), nullable=True))
    op.add_column("products", sa.Column("category_normalized", sa.String(length=100), nullable=True))

    bind = op.get_bind()
    session = Session(bind=bind)

    rows = session.execute(
        sa.text("SELECT id, name, brand, category FROM products")
    ).fetchall()

    for row in rows:
        session.execute(
            sa.text(
                """
                UPDATE products
                SET name_normalized = :name_normalized,
                    brand_normalized = :brand_normalized,
                    category_normalized = :category_normalized
                WHERE id = :id
                """
            ),
            {
                "id": row.id,
                "name_normalized": _normalize(row.name),
                "brand_normalized": _normalize(row.brand),
                "category_normalized": _normalize(row.category),
            },
        )

    session.commit()

    op.alter_column("products", "name_normalized", nullable=False)
    op.alter_column("products", "brand_normalized", nullable=False)
    op.alter_column("products", "category_normalized", nullable=False)

    op.create_index(op.f("ix_products_brand_normalized"), "products", ["brand_normalized"], unique=False)
    op.create_index(op.f("ix_products_category_normalized"), "products", ["category_normalized"], unique=False)
    op.create_index(op.f("ix_products_name_normalized"), "products", ["name_normalized"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_products_name_normalized"), table_name="products")
    op.drop_index(op.f("ix_products_category_normalized"), table_name="products")
    op.drop_index(op.f("ix_products_brand_normalized"), table_name="products")
    op.drop_column("products", "category_normalized")
    op.drop_column("products", "brand_normalized")
    op.drop_column("products", "name_normalized")