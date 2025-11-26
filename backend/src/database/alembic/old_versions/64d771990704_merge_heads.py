"""merge heads

Revision ID: 64d771990704
Revises: aa282b509ddb, b7c780098f52
Create Date: 2025-11-26 13:20:26.509890

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64d771990704'
down_revision: Union[str, Sequence[str], None] = ('aa282b509ddb', 'b7c780098f52')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
