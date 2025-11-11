"""add unique constraint on dedup_hash

Revision ID: 023_unique_dedup
Revises: 022_production_baseline
Create Date: 2025-11-05

SECURITY FIX: Prevents race condition in deduplication.

GPT-5 Pro audit finding: Two Celery workers could simultaneously check
for duplicate, both find nothing, both insert → duplicate events.

This migration adds a UNIQUE constraint on events.dedup_hash to
prevent this race condition at the database level.

Note: Uses CREATE UNIQUE INDEX to handle NULL values properly
(UNIQUE constraint would allow multiple NULLs, which we don't want to block).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '023_unique_dedup'
down_revision: Union[str, None] = '022_production_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add UNIQUE constraint on events.dedup_hash.
    
    This prevents duplicate events from being inserted via race conditions
    when multiple Celery workers process the same content simultaneously.
    
    Uses partial unique index to allow NULL values (fixture data may not have dedup_hash).
    """
    
    # SECURITY: Add unique constraint on dedup_hash (non-NULL only)
    # Using partial index: UNIQUE WHERE dedup_hash IS NOT NULL
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_events_dedup_hash_unique 
        ON events(dedup_hash)
        WHERE dedup_hash IS NOT NULL;
    """)
    
    # Also ensure content_hash is unique (fallback dedup mechanism)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_events_content_hash_unique 
        ON events(content_hash)
        WHERE content_hash IS NOT NULL;
    """)


def downgrade() -> None:
    """Remove unique constraints."""
    
    op.execute("DROP INDEX IF EXISTS idx_events_content_hash_unique")
    op.execute("DROP INDEX IF EXISTS idx_events_dedup_hash_unique")

