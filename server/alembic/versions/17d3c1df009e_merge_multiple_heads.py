"""merge multiple heads

Revision ID: 17d3c1df009e
Revises: 5153491fc6ca, b7e2c4a9f1d6
Create Date: 2026-09-09 22:17:53.308293

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17d3c1df009e'
down_revision: Union[str, None] = ('5153491fc6ca', 'b7e2c4a9f1d6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
