"""Merge migration branches

Revision ID: 015_merge_branches
Revises: 014_add_source_credibility_snapshots, 20251020115051
Create Date: 2025-10-22

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '015_merge_branches'
down_revision: Union[str, Sequence[str], None] = ('014_add_source_credibility_snapshots', '20251020115051')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No schema changes needed - this is a merge migration
    pass


def downgrade() -> None:
    # No downgrade needed - this is a merge migration
    pass

