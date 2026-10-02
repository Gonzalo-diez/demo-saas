"""fixes new

Revision ID: 5153491fc6ca
Revises: a7ea019535e6
Create Date: 2024-03-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5153491fc6ca'
down_revision: Union[str, None] = 'a7ea019535e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Se agrega if_exists=True para evitar fallos si el índice o la tabla ya fueron eliminados
    op.drop_index(
        'ix_online_customer_payment_allocations_sales_invoice_id',
        table_name='online_customer_payment_allocations',
        if_exists=True
    )
    
    # Si la migración intenta eliminar la tabla completa o más índices, asegúrate de usar if_exists=True:
    # op.drop_table('online_customer_payment_allocations', if_exists=True)


def downgrade() -> None:
    pass