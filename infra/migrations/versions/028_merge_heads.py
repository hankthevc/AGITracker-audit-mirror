"""merge migration heads

Revision ID: 028_merge_heads
Revises: 023_dedup_hash_unique, 027_rich_metadata
Create Date: 2025-11-06

MERGE MIGRATION: Resolves multiple migration heads into a single chain.

This migration does NO schema changes - it only merges two parallel
migration branches that both started from 022_production_baseline:

Branch 1 (production): 022 → 023_dedup_hash_unique → (no further migrations)
Branch 2 (development): 022 → 023_unique_dedup → 024 → 025 → 026 → 027

After this merge, all future migrations will have a single linear history.

Policy: Never modify or delete existing migrations. Always use merge
migrations to resolve multiple heads.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '028_merge_heads'
down_revision: Union[str, Sequence[str], None] = ('023_dedup_hash_unique', '027_rich_metadata')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Merge migration - no schema changes.
    
    Both branches have been applied to their respective environments.
    This migration simply unifies them into a single head.
    """
    print("✓ Merged migration heads: 023_dedup_hash_unique + 027_rich_metadata")


def downgrade() -> None:
    """
    Downgrade splits back into two heads.
    
    This is expected behavior for a merge migration.
    """
    print("✓ Split back into two heads")

