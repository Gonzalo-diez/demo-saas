"""add sales_invoice_payments table (cobros online contra entrega)

Revision ID: d5e3a7c1f9b2
Revises: c2d4f8a91b3e
Create Date: 2026-07-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e3a7c1f9b2'
down_revision: Union[str, None] = 'c2d4f8a91b3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'sales_invoice_payments',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column(
            'sales_invoice_id',
            sa.Integer(),
            sa.ForeignKey('sales_invoices.id'),
            nullable=False,
            index=True,
        ),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('payment_method', sa.String(length=30), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column(
            'created_by',
            sa.Integer(),
            sa.ForeignKey('sales_reps.id'),
            nullable=True,
            index=True,
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('sales_invoice_payments')
