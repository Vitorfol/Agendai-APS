"""remove status_vinculo from convidado

Revision ID: f2g3h4i5j6k7
Revises: d68dc225510c
Create Date: 2025-12-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2g3h4i5j6k7'
down_revision: Union[str, None] = '1920ebed8eac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove coluna status_vinculo da tabela convidado
    op.drop_column('convidado', 'status_vinculo')


def downgrade() -> None:
    # Recriar coluna status_vinculo (caso necessite reverter)
    op.add_column('convidado', 
        sa.Column('status_vinculo', sa.String(255), nullable=True)
    )
