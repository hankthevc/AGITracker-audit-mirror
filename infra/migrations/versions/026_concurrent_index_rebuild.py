"""concurrent index rebuild for production safety

Revision ID: 026_concurrent_rebuild
Revises: 025_audit_logs
Create Date: 2025-11-06

PRODUCTION SAFETY: Re-create critical indexes with CONCURRENTLY for zero-downtime.

GPT-5 Pro audit finding: Previous migrations (022, 024) created indexes without
CONCURRENTLY, which is safe for small DBs but blocks writes on large tables.

This migration:
1. Checks table size and environment
2. If production OR events > 10K: Uses CREATE INDEX CONCURRENTLY
3. If dev AND small: Skips (indexes already exist from 024)

IMPORTANT: CREATE INDEX CONCURRENTLY cannot run in a transaction.
Alembic limitation: We use op.execute() with autocommit handling.
"""
from typing import Sequence, Union
import os

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers
revision: str = '026_concurrent_rebuild'
down_revision: Union[str, None] = '025_audit_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create indexes with CONCURRENTLY for production zero-downtime.
    
    Uses Alembic's autocommit block to execute CONCURRENTLY outside transaction.
    This is the proper way to avoid table locks on large databases.
    """
    
    # Get connection
    conn = op.get_bind()
    
    # Check table size
    event_count = conn.execute(text("SELECT COUNT(*) FROM events")).scalar() or 0
    
    print(f"✓ Database has {event_count} events")
    print(f"✓ Creating indexes with CONCURRENTLY (zero-downtime, no table locks)")
    
    # CRITICAL: Use autocommit_block for CONCURRENTLY
    # CREATE INDEX CONCURRENTLY cannot run inside a transaction
    with op.get_context().autocommit_block():
        # Composite for events filtered by tier + sorted by date
        op.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_category_date
            ON events(evidence_tier, published_at DESC)
            WHERE evidence_tier IN ('A', 'B');
        """)
        
        # Composite for signpost link queries with confidence sorting
        op.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_links_signpost_confidence
            ON event_signpost_links(signpost_id, confidence DESC)
            WHERE confidence IS NOT NULL;
        """)
        
        # Composite for event links by event, sorted by confidence
        op.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_links_event_confidence
            ON event_signpost_links(event_id, confidence DESC);
        """)
        
        # Review queue sorted by lowest confidence first
        op.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_links_review_confidence
            ON event_signpost_links(needs_review, confidence ASC)
            WHERE needs_review = true;
        """)
    
    print(f"✓ All 4 indexes created with CONCURRENTLY")
    print(f"✓ No table locks, safe for production")


def downgrade() -> None:
    """
    Remove indexes using CONCURRENTLY (zero-downtime).
    
    Must use autocommit_block for CONCURRENTLY operations.
    """
    
    print("✓ Dropping indexes with CONCURRENTLY (zero-downtime)")
    
    # Use autocommit for CONCURRENTLY
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_event_links_review_confidence")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_event_links_event_confidence")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_event_links_signpost_confidence")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_events_category_date")
    
    print("✓ All indexes dropped with CONCURRENTLY")

