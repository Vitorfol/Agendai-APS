"""add id to disciplina_dias

Revision ID: e1f2a3b4c5d6
Revises: d68dc225510c
Create Date: 2025-12-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd68dc225510c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Drop the foreign key constraint first
    op.execute('ALTER TABLE disciplina_dias DROP FOREIGN KEY disciplina_dias_ibfk_1')
    
    # Step 2: Drop the current primary key constraint
    op.execute('ALTER TABLE disciplina_dias DROP PRIMARY KEY')
    
    # Step 3: Add new id column as primary key (autoincrement)
    op.execute('''
        ALTER TABLE disciplina_dias 
        ADD COLUMN id INT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST
    ''')
    
    # Step 4: Recreate the foreign key constraint
    op.execute('''
        ALTER TABLE disciplina_dias 
        ADD CONSTRAINT disciplina_dias_ibfk_1 
        FOREIGN KEY (id_disciplina) REFERENCES disciplina (id_evento)
    ''')
    
    # Step 5: Add unique constraint on (id_disciplina, dia) to maintain logical uniqueness
    op.create_unique_constraint(
        'ux_disciplina_dia', 
        'disciplina_dias', 
        ['id_disciplina', 'dia']
    )
    
    # Step 6: Ensure columns are NOT NULL
    op.alter_column('disciplina_dias', 'id_disciplina',
                    existing_type=sa.Integer(),
                    nullable=False)
    op.alter_column('disciplina_dias', 'dia',
                    existing_type=sa.String(10),
                    nullable=False)


def downgrade() -> None:
    # Reverse the changes
    op.drop_constraint('ux_disciplina_dia', 'disciplina_dias', type_='unique')
    op.execute('ALTER TABLE disciplina_dias DROP FOREIGN KEY disciplina_dias_ibfk_1')
    op.execute('ALTER TABLE disciplina_dias DROP COLUMN id')
    op.execute('ALTER TABLE disciplina_dias ADD PRIMARY KEY (id_disciplina, dia)')
    op.execute('''
        ALTER TABLE disciplina_dias 
        ADD CONSTRAINT disciplina_dias_ibfk_1 
        FOREIGN KEY (id_disciplina) REFERENCES disciplina (id_evento)
    ''')
