from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision: str = 'a3649290ef79'
down_revision: Union[str, None] = 'e12a764fe301'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 👇 DEFINÍ EL ENUM UNA VEZ
order_type_enum = postgresql.ENUM(
    'ONLINE',
    'B2B',
    name='order_type_enum'
)


def upgrade() -> None:
    # ✅ 1. Crear el ENUM
    order_type_enum.create(op.get_bind(), checkfirst=True)

    # ✅ 2. Agregar columna
    op.add_column(
        'orders',
        sa.Column(
            'order_type',
            order_type_enum,
            server_default='ONLINE',
            nullable=False
        )
    )

    # ✅ 3. Resto de cambios
    op.alter_column('orders', 'customer_name',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)

    op.alter_column('orders', 'customer_phone',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)

    op.alter_column('orders', 'customer_email',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)

    op.alter_column('orders', 'delivery_type',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)

    op.alter_column('orders', 'delivery_address',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)

    op.alter_column('orders', 'delivery_city',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)

    # ⚠️ IMPORTANTE: este debería ser nullable=True (como vimos antes)
    op.alter_column('orders', 'total_cost',
               existing_type=sa.NUMERIC(precision=12, scale=2),
               nullable=True)

    op.alter_column('orders', 'total_amount',
               existing_type=sa.NUMERIC(precision=12, scale=2),
               nullable=False)


def downgrade() -> None:
    # 🔥 1. Dropear columna primero
    op.drop_column('orders', 'order_type')

    # 🔥 2. Dropear enum
    order_type_enum.drop(op.get_bind(), checkfirst=True)

    # 🔁 Revertir cambios
    op.alter_column('orders', 'total_amount',
               existing_type=sa.NUMERIC(precision=12, scale=2),
               nullable=True)

    op.alter_column('orders', 'total_cost',
               existing_type=sa.NUMERIC(precision=12, scale=2),
               nullable=False)

    op.alter_column('orders', 'delivery_city',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)

    op.alter_column('orders', 'delivery_address',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)

    op.alter_column('orders', 'delivery_type',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)

    op.alter_column('orders', 'customer_email',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)

    op.alter_column('orders', 'customer_phone',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)

    op.alter_column('orders', 'customer_name',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)