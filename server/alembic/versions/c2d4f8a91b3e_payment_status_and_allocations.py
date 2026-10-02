"""add payment_status/paid_amount to invoices and payment allocation tables

Revision ID: c2d4f8a91b3e
Revises: 7fa8baf710e5
Create Date: 2026-07-21 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d4f8a91b3e'
down_revision: Union[str, None] = '7fa8baf710e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- sales_invoices ---
    op.add_column(
        'sales_invoices',
        sa.Column('payment_status', sa.String(length=20), nullable=False, server_default='pending'),
    )
    op.add_column(
        'sales_invoices',
        sa.Column('paid_amount', sa.Numeric(12, 2), nullable=False, server_default='0.00'),
    )
    op.create_index(
        op.f('ix_sales_invoices_payment_status'),
        'sales_invoices',
        ['payment_status'],
    )

    # --- purchase_invoices ---
    op.add_column(
        'purchase_invoices',
        sa.Column('payment_status', sa.String(length=20), nullable=False, server_default='pending'),
    )
    op.add_column(
        'purchase_invoices',
        sa.Column('paid_amount', sa.Numeric(12, 2), nullable=False, server_default='0.00'),
    )
    op.create_index(
        op.f('ix_purchase_invoices_payment_status'),
        'purchase_invoices',
        ['payment_status'],
    )

    # --- client_payment_allocations ---
    op.create_table(
        'client_payment_allocations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column(
            'client_account_movement_id',
            sa.Integer(),
            sa.ForeignKey('client_account_movements.id'),
            nullable=False,
            index=True,
        ),
        sa.Column(
            'sales_invoice_id',
            sa.Integer(),
            sa.ForeignKey('sales_invoices.id'),
            nullable=False,
            index=True,
        ),
        sa.Column('amount_applied', sa.Numeric(12, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- supplier_payment_allocations ---
    op.create_table(
        'supplier_payment_allocations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column(
            'supplier_account_movement_id',
            sa.Integer(),
            sa.ForeignKey('supplier_account_movements.id'),
            nullable=False,
            index=True,
        ),
        sa.Column(
            'purchase_invoice_id',
            sa.Integer(),
            sa.ForeignKey('purchase_invoices.id'),
            nullable=False,
            index=True,
        ),
        sa.Column('amount_applied', sa.Numeric(12, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('supplier_payment_allocations')
    op.drop_table('client_payment_allocations')

    op.drop_index(op.f('ix_purchase_invoices_payment_status'), table_name='purchase_invoices')
    op.drop_column('purchase_invoices', 'paid_amount')
    op.drop_column('purchase_invoices', 'payment_status')

    op.drop_index(op.f('ix_sales_invoices_payment_status'), table_name='sales_invoices')
    op.drop_column('sales_invoices', 'paid_amount')
    op.drop_column('sales_invoices', 'payment_status')
