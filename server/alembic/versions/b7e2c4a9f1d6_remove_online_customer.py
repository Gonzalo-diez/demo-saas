"""remove online_customer (compradores online reemplazados por Client logueado)

Ya no existen compradores "online" anónimos: para ver el catálogo y
comprar hace falta ser un Client registrado por el admin y logueado, así
que todo pedido/remito queda ligado directamente a un client_id. Esto
deja sin uso todo el modelo OnlineCustomer (cuenta corriente, pagos y
analytics propios), que se borra por completo.

No hay datos que migrar: estas tablas nunca llegaron a tener
compradores reales cargados en producción.

Revision ID: b7e2c4a9f1d6
Revises: e3279fcddde6
Create Date: 2026-09-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e2c4a9f1d6'
down_revision: Union[str, None] = 'e3279fcddde6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Eliminación idempotente con CASCADE (borra tablas e índices asociados si existen)
    op.execute("DROP TABLE IF EXISTS analytics_online_customer_daily CASCADE")
    op.execute("DROP TABLE IF EXISTS online_customer_payment_allocations CASCADE")
    op.execute("DROP TABLE IF EXISTS online_customer_account_movements CASCADE")

    # Limpieza en sales_invoices
    op.execute("ALTER TABLE sales_invoices DROP CONSTRAINT IF EXISTS sales_invoices_online_customer_id_fkey")
    op.execute("DROP INDEX IF EXISTS ix_sales_invoices_online_customer_id")
    op.execute("ALTER TABLE sales_invoices DROP COLUMN IF EXISTS online_customer_id")

    # Tabla principal
    op.execute("DROP TABLE IF EXISTS online_customers CASCADE")


def downgrade() -> None:
    op.create_table(
        'online_customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_normalized', sa.String(length=255), nullable=True),
        sa.Column('phone_normalized', sa.String(length=50), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('current_balance', sa.Numeric(12, 2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_online_customers_email_normalized'),
        'online_customers', ['email_normalized'], unique=True,
    )
    op.create_index(op.f('ix_online_customers_id'), 'online_customers', ['id'], unique=False)
    op.create_index(
        op.f('ix_online_customers_phone_normalized'),
        'online_customers', ['phone_normalized'], unique=True,
    )

    op.add_column('sales_invoices', sa.Column('online_customer_id', sa.Integer(), nullable=True))
    op.create_index(
        op.f('ix_sales_invoices_online_customer_id'),
        'sales_invoices', ['online_customer_id'], unique=False,
    )
    op.create_foreign_key(
        'sales_invoices_online_customer_id_fkey',
        'sales_invoices', 'online_customers', ['online_customer_id'], ['id'],
    )

    op.create_table(
        'online_customer_account_movements',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('online_customer_id', sa.Integer(), sa.ForeignKey('online_customers.id'), nullable=False, index=True),
        sa.Column('movement_type', sa.String(length=50), nullable=False, index=True),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('balance_before', sa.Numeric(12, 2), nullable=False),
        sa.Column('balance_after', sa.Numeric(12, 2), nullable=False),
        sa.Column('reference_type', sa.String(length=50), nullable=True, index=True),
        sa.Column('reference_id', sa.Integer(), nullable=True, index=True),
        sa.Column('payment_method', sa.String(length=30), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'online_customer_payment_allocations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('online_customer_account_movement_id', sa.Integer(), nullable=False),
        sa.Column('sales_invoice_id', sa.Integer(), nullable=False),
        sa.Column('amount_applied', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['online_customer_account_movement_id'], ['online_customer_account_movements.id']),
        sa.ForeignKeyConstraint(['sales_invoice_id'], ['sales_invoices.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_online_customer_payment_allocations_id'),
        'online_customer_payment_allocations', ['id'], unique=False,
    )
    op.create_index(
        op.f('ix_online_customer_payment_allocations_online_customer_account_movement_id'),
        'online_customer_payment_allocations', ['online_customer_account_movement_id'], unique=False,
    )
    op.create_index(
        op.f('ix_online_customer_payment_allocations_sales_invoice_id'),
        'online_customer_payment_allocations', ['sales_invoice_id'], unique=False,
    )

    op.create_table(
        'analytics_online_customer_daily',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('online_customer_id', sa.Integer(), nullable=False),
        sa.Column('total_orders', sa.Integer(), nullable=False),
        sa.Column('revenue_generated', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('cost_generated', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('margin_generated', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('products_bought', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('unique_products_count', sa.Integer(), nullable=False),
        sa.Column('categories_summary', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['online_customer_id'], ['online_customers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'online_customer_id', name='uq_analytics_online_customer_daily_date_customer'),
    )
    op.create_index(
        op.f('ix_analytics_online_customer_daily_date'),
        'analytics_online_customer_daily', ['date'], unique=False,
    )
    op.create_index(
        op.f('ix_analytics_online_customer_daily_online_customer_id'),
        'analytics_online_customer_daily', ['online_customer_id'], unique=False,
    )