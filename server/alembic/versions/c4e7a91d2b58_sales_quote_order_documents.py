"""presupuestos como documento de venta de un pedido + imputaciones a presupuestos

Revision ID: c4e7a91d2b58
Revises: aa86432a02f3
Create Date: 2026-09-23 21:00:00.000000

- orders.document_type ('sales_invoice' | 'sales_quote')
- sales_quotes: datos del pedido (order_id, sales_type, sucursal, customer_*,
  entrega, snapshots), cobro (payment_status, paid_amount), costos y margen.
  client_name / client_tax_id pasan a customer_name / customer_tax_id.
- sales_quote_items: marca y costos
- purchase_quotes: payment_status / paid_amount
- client_payment_allocations / supplier_payment_allocations: pueden imputarse
  a un presupuesto (sales_quote_id / purchase_quote_id) en vez de a un remito.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c4e7a91d2b58'
down_revision: Union[str, None] = 'aa86432a02f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# El tipo ya existe (lo crearon orders y sales_invoices): no recrearlo.
sales_type_enum = postgresql.ENUM('B2B', 'ONLINE', name='sales_type_enum', create_type=False)


def upgrade() -> None:
    # ------------------------------------------------------------ orders
    op.add_column('orders', sa.Column('document_type', sa.String(length=20), server_default='sales_invoice', nullable=False))
    op.create_check_constraint(
        'ck_order_document_type', 'orders',
        "document_type IN ('sales_invoice', 'sales_quote')",
    )

    # ------------------------------------------------------ sales_quotes
    op.add_column('sales_quotes', sa.Column('order_id', sa.Integer(), nullable=True))
    op.add_column('sales_quotes', sa.Column('sales_type', sales_type_enum, nullable=True))
    op.add_column('sales_quotes', sa.Column('client_branch_id', sa.Integer(), nullable=True))
    op.add_column('sales_quotes', sa.Column('customer_name', sa.String(length=255), nullable=True))
    op.add_column('sales_quotes', sa.Column('customer_tax_id', sa.String(length=50), nullable=True))
    op.add_column('sales_quotes', sa.Column('customer_phone', sa.String(length=50), nullable=True))
    op.add_column('sales_quotes', sa.Column('customer_email', sa.String(length=255), nullable=True))
    op.add_column('sales_quotes', sa.Column('delivery_type', sa.String(length=20), nullable=True))
    op.add_column('sales_quotes', sa.Column('delivery_address', sa.String(length=255), nullable=True))
    op.add_column('sales_quotes', sa.Column('delivery_city', sa.String(length=120), nullable=True))
    op.add_column('sales_quotes', sa.Column('delivery_reference', sa.Text(), nullable=True))
    op.add_column('sales_quotes', sa.Column('client_branch_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('sales_quotes', sa.Column('sales_rep_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('sales_quotes', sa.Column('payment_status', sa.String(length=20), server_default='pending', nullable=False))
    op.add_column('sales_quotes', sa.Column('paid_amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False))
    op.add_column('sales_quotes', sa.Column('total_cost', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('sales_quotes', sa.Column('margin_amount', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('sales_quotes', sa.Column('currency', sa.String(length=10), server_default='ARS', nullable=False))
    op.add_column('sales_quotes', sa.Column('pdf_generated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('sales_quotes', sa.Column('email_sent_at', sa.DateTime(timezone=True), nullable=True))

    # Datos existentes: todas eran cotizaciones sueltas cargadas por el personal.
    op.execute("UPDATE sales_quotes SET sales_type = 'B2B', customer_name = client_name, customer_tax_id = client_tax_id")
    op.alter_column('sales_quotes', 'sales_type', existing_type=sales_type_enum, nullable=False)

    op.drop_index('ix_sales_quotes_client_name', table_name='sales_quotes')
    op.drop_column('sales_quotes', 'client_name')
    op.drop_column('sales_quotes', 'client_tax_id')

    op.create_foreign_key('fk_sales_quotes_order_id', 'sales_quotes', 'orders', ['order_id'], ['id'])
    op.create_foreign_key('fk_sales_quotes_client_branch_id', 'sales_quotes', 'client_branches', ['client_branch_id'], ['id'])
    op.create_unique_constraint('uq_sales_quote_order_id', 'sales_quotes', ['order_id'])
    op.create_index(op.f('ix_sales_quotes_order_id'), 'sales_quotes', ['order_id'], unique=False)
    op.create_index(op.f('ix_sales_quotes_sales_type'), 'sales_quotes', ['sales_type'], unique=False)
    op.create_index(op.f('ix_sales_quotes_client_branch_id'), 'sales_quotes', ['client_branch_id'], unique=False)
    op.create_index(op.f('ix_sales_quotes_customer_name'), 'sales_quotes', ['customer_name'], unique=False)
    op.create_index(op.f('ix_sales_quotes_customer_email'), 'sales_quotes', ['customer_email'], unique=False)
    op.create_index(op.f('ix_sales_quotes_payment_status'), 'sales_quotes', ['payment_status'], unique=False)

    op.drop_constraint('ck_sales_quote_status', 'sales_quotes', type_='check')
    op.create_check_constraint(
        'ck_sales_quote_status', 'sales_quotes',
        "status IN ('draft', 'sent', 'approved', 'rejected', 'expired', 'cancelled')",
    )

    # ------------------------------------------------- sales_quote_items
    op.add_column('sales_quote_items', sa.Column('product_brand', sa.String(length=255), nullable=True))
    op.add_column('sales_quote_items', sa.Column('unit_cost', sa.Numeric(precision=12, scale=4), nullable=True))
    op.add_column('sales_quote_items', sa.Column('subtotal_cost', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('sales_quote_items', sa.Column('margin_amount', sa.Numeric(precision=12, scale=2), nullable=True))

    # --------------------------------------------------- purchase_quotes
    op.add_column('purchase_quotes', sa.Column('payment_status', sa.String(length=20), server_default='pending', nullable=False))
    op.add_column('purchase_quotes', sa.Column('paid_amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False))
    op.create_index(op.f('ix_purchase_quotes_payment_status'), 'purchase_quotes', ['payment_status'], unique=False)

    # ------------------------------------------ client_payment_allocations
    op.alter_column('client_payment_allocations', 'sales_invoice_id', existing_type=sa.Integer(), nullable=True)
    op.add_column('client_payment_allocations', sa.Column('sales_quote_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_client_payment_allocations_sales_quote_id', 'client_payment_allocations', 'sales_quotes', ['sales_quote_id'], ['id'])
    op.create_index(op.f('ix_client_payment_allocations_sales_quote_id'), 'client_payment_allocations', ['sales_quote_id'], unique=False)
    op.create_check_constraint(
        'ck_client_payment_allocation_one_document', 'client_payment_allocations',
        "(sales_invoice_id IS NOT NULL AND sales_quote_id IS NULL) "
        "OR (sales_invoice_id IS NULL AND sales_quote_id IS NOT NULL)",
    )

    # ------------------------------------------ supplier_payment_allocations
    op.alter_column('supplier_payment_allocations', 'purchase_invoice_id', existing_type=sa.Integer(), nullable=True)
    op.add_column('supplier_payment_allocations', sa.Column('purchase_quote_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_supplier_payment_allocations_purchase_quote_id', 'supplier_payment_allocations', 'purchase_quotes', ['purchase_quote_id'], ['id'])
    op.create_index(op.f('ix_supplier_payment_allocations_purchase_quote_id'), 'supplier_payment_allocations', ['purchase_quote_id'], unique=False)
    op.create_check_constraint(
        'ck_supplier_payment_allocation_one_document', 'supplier_payment_allocations',
        "(purchase_invoice_id IS NOT NULL AND purchase_quote_id IS NULL) "
        "OR (purchase_invoice_id IS NULL AND purchase_quote_id IS NOT NULL)",
    )


def downgrade() -> None:
    # Las imputaciones a presupuestos no tienen equivalente en el esquema anterior.
    op.execute("DELETE FROM supplier_payment_allocations WHERE purchase_quote_id IS NOT NULL")
    op.drop_constraint('ck_supplier_payment_allocation_one_document', 'supplier_payment_allocations', type_='check')
    op.drop_index(op.f('ix_supplier_payment_allocations_purchase_quote_id'), table_name='supplier_payment_allocations')
    op.drop_constraint('fk_supplier_payment_allocations_purchase_quote_id', 'supplier_payment_allocations', type_='foreignkey')
    op.drop_column('supplier_payment_allocations', 'purchase_quote_id')
    op.alter_column('supplier_payment_allocations', 'purchase_invoice_id', existing_type=sa.Integer(), nullable=False)

    op.execute("DELETE FROM client_payment_allocations WHERE sales_quote_id IS NOT NULL")
    op.drop_constraint('ck_client_payment_allocation_one_document', 'client_payment_allocations', type_='check')
    op.drop_index(op.f('ix_client_payment_allocations_sales_quote_id'), table_name='client_payment_allocations')
    op.drop_constraint('fk_client_payment_allocations_sales_quote_id', 'client_payment_allocations', type_='foreignkey')
    op.drop_column('client_payment_allocations', 'sales_quote_id')
    op.alter_column('client_payment_allocations', 'sales_invoice_id', existing_type=sa.Integer(), nullable=False)

    op.drop_index(op.f('ix_purchase_quotes_payment_status'), table_name='purchase_quotes')
    op.drop_column('purchase_quotes', 'paid_amount')
    op.drop_column('purchase_quotes', 'payment_status')

    op.drop_column('sales_quote_items', 'margin_amount')
    op.drop_column('sales_quote_items', 'subtotal_cost')
    op.drop_column('sales_quote_items', 'unit_cost')
    op.drop_column('sales_quote_items', 'product_brand')

    # Los presupuestos que nacieron de pedidos no existían en el esquema anterior.
    op.execute("DELETE FROM sales_quote_items WHERE sales_quote_id IN (SELECT id FROM sales_quotes WHERE order_id IS NOT NULL)")
    op.execute("DELETE FROM sales_quotes WHERE order_id IS NOT NULL")
    op.execute("UPDATE sales_quotes SET status = 'rejected' WHERE status = 'cancelled'")
    op.drop_constraint('ck_sales_quote_status', 'sales_quotes', type_='check')
    op.create_check_constraint(
        'ck_sales_quote_status', 'sales_quotes',
        "status IN ('draft', 'sent', 'approved', 'rejected', 'expired')",
    )

    op.add_column('sales_quotes', sa.Column('client_name', sa.String(length=255), nullable=True))
    op.add_column('sales_quotes', sa.Column('client_tax_id', sa.String(length=50), nullable=True))
    op.execute("UPDATE sales_quotes SET client_name = customer_name, client_tax_id = customer_tax_id")
    op.create_index('ix_sales_quotes_client_name', 'sales_quotes', ['client_name'], unique=False)

    op.drop_index(op.f('ix_sales_quotes_payment_status'), table_name='sales_quotes')
    op.drop_index(op.f('ix_sales_quotes_customer_email'), table_name='sales_quotes')
    op.drop_index(op.f('ix_sales_quotes_customer_name'), table_name='sales_quotes')
    op.drop_index(op.f('ix_sales_quotes_client_branch_id'), table_name='sales_quotes')
    op.drop_index(op.f('ix_sales_quotes_sales_type'), table_name='sales_quotes')
    op.drop_index(op.f('ix_sales_quotes_order_id'), table_name='sales_quotes')
    op.drop_constraint('uq_sales_quote_order_id', 'sales_quotes', type_='unique')
    op.drop_constraint('fk_sales_quotes_client_branch_id', 'sales_quotes', type_='foreignkey')
    op.drop_constraint('fk_sales_quotes_order_id', 'sales_quotes', type_='foreignkey')
    for col in (
        'email_sent_at', 'pdf_generated_at', 'currency', 'margin_amount', 'total_cost',
        'paid_amount', 'payment_status', 'sales_rep_snapshot', 'client_branch_snapshot',
        'delivery_reference', 'delivery_city', 'delivery_address', 'delivery_type',
        'customer_email', 'customer_phone', 'customer_tax_id', 'customer_name',
        'client_branch_id', 'sales_type', 'order_id',
    ):
        op.drop_column('sales_quotes', col)

    op.drop_constraint('ck_order_document_type', 'orders', type_='check')
    op.drop_column('orders', 'document_type')
