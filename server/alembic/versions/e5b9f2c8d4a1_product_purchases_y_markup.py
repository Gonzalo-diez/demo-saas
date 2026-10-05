"""historial de compras por producto + % de remarque

Revision ID: e5b9f2c8d4a1
Revises: d4a8e1b7c3f9
Create Date: 2026-10-04 12:00:00

- product_purchases: cada compra de un producto (cantidad, costo, precio de venta fijado,
  % de remarque, vencimiento, origen). Es un registro: no se edita ni se borra.
- products.markup_percent: % de remarque sobre el costo con el que se calculó el precio.
- Backfill: los productos que ya tenían stock reciben UNA entrada inicial con su stock y
  costo actuales (sin vencimiento), para que el historial no arranque vacío.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5b9f2c8d4a1"
down_revision: Union[str, None] = "d4a8e1b7c3f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products", sa.Column("markup_percent", sa.Numeric(7, 2), nullable=True)
    )

    op.create_table(
        "product_purchases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Integer(),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("markup_percent", sa.Numeric(7, 2), nullable=True),
        sa.Column("sale_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="manual"),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("sales_reps.id"), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("quantity > 0", name="ck_product_purchases_quantity_positive"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_product_purchases_cost_non_negative"),
    )
    op.create_index("ix_product_purchases_id", "product_purchases", ["id"])
    op.create_index("ix_product_purchases_tenant_id", "product_purchases", ["tenant_id"])
    op.create_index("ix_product_purchases_product_id", "product_purchases", ["product_id"])
    op.create_index("ix_product_purchases_purchase_date", "product_purchases", ["purchase_date"])
    op.create_index("ix_product_purchases_expiry_date", "product_purchases", ["expiry_date"])

    op.execute(
        """
        INSERT INTO product_purchases
            (tenant_id, product_id, purchase_date, quantity, unit_cost, sale_price,
             source, notes)
        SELECT tenant_id, id, CURRENT_DATE, stock_current, COALESCE(unit_cost, 0),
               unit_price, 'initial_stock', 'Stock existente al activar el historial'
        FROM products
        WHERE stock_current > 0
        """
    )


def downgrade() -> None:
    op.drop_index("ix_product_purchases_expiry_date", table_name="product_purchases")
    op.drop_index("ix_product_purchases_purchase_date", table_name="product_purchases")
    op.drop_index("ix_product_purchases_product_id", table_name="product_purchases")
    op.drop_index("ix_product_purchases_tenant_id", table_name="product_purchases")
    op.drop_index("ix_product_purchases_id", table_name="product_purchases")
    op.drop_table("product_purchases")
    op.drop_column("products", "markup_percent")
