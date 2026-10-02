"""empty message

Revision ID: 7fa8baf710e5
Revises: 60cecc3cdbd8, b7a1c9f3e2d4
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fa8baf710e5'
down_revision: Union[str, Sequence[str], None] = ('60cecc3cdbd8', 'b7a1c9f3e2d4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
