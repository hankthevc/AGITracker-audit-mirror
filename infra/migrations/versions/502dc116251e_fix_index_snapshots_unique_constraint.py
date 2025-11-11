"""Fix index_snapshots unique constraint

Revision ID: 502dc116251e
Revises: 001_initial
Create Date: 2025-10-14 14:23:33.791233

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '502dc116251e'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old unique constraint on as_of_date only
    op.drop_constraint('index_snapshots_as_of_date_key', 'index_snapshots', type_='unique')
    
    # Add new unique constraint on (as_of_date, preset)
    op.create_unique_constraint(
        'index_snapshots_as_of_date_preset_key',
        'index_snapshots',
        ['as_of_date', 'preset']
    )


def downgrade() -> None:
    # Revert to old constraint
    op.drop_constraint('index_snapshots_as_of_date_preset_key', 'index_snapshots', type_='unique')
    op.create_unique_constraint('index_snapshots_as_of_date_key', 'index_snapshots', ['as_of_date'])

