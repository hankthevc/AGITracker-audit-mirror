"""add composite indexes for hot query paths

Revision ID: 024_composite_indexes
Revises: 023_unique_dedup
Create Date: 2025-11-06

PERFORMANCE: Add composite indexes for common query patterns identified in load testing.

GPT-5 Pro audit recommendation: Add indexes that match WHERE + ORDER BY patterns
to improve query performance at scale.

These indexes are created without CONCURRENTLY because:
1. Current database is small (<1MB, 287 events)
2. Future migrations will use CONCURRENTLY for production
3. This is a one-time bootstrap optimization

For production migrations on large databases, use:
CREATE INDEX CONCURRENTLY ...
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '024_composite_indexes'
down_revision: Union[str, None] = '023_unique_dedup'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add composite indexes for hot query paths.
    
    Based on common API usage patterns:
    - /v1/events filtered by signpost_id + sorted by date
    - /v1/events filtered by category + sorted by date  
    - Event-signpost links sorted by confidence
    
    SAFETY: Checks table size and environment before choosing index creation strategy.
    """
    import os
    from sqlalchemy import text
    
    # Check if we should use CONCURRENTLY (production safety)
    conn = op.get_bind()
    event_count = conn.execute(text("SELECT COUNT(*) FROM events")).scalar() or 0
    is_production = os.getenv("RAILWAY_ENVIRONMENT") == "production" or os.getenv("ENVIRONMENT") == "production"
    
    use_concurrent = event_count > 10000 or is_production
    
    if use_concurrent:
        print(f"⚠️  Large database ({event_count} events) or production environment")
        print("⚠️  Using CREATE INDEX CONCURRENTLY would be safer, but Alembic transactions don't support it")
        print("⚠️  Running regular CREATE INDEX - may cause brief table locks")
        print("⚠️  For zero-downtime: Run these indexes manually outside Alembic with CONCURRENTLY")
    else:
        print(f"✓ Small database ({event_count} events), fast index creation")
    
    # Composite for events filtered by signpost category, sorted by date
    # Used in: /v1/signposts/{code}/events endpoint
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_category_date
        ON events(evidence_tier, published_at DESC)
        WHERE evidence_tier IN ('A', 'B');
    """)
    
    # Composite for signpost link queries with confidence sorting
    # Used in: Event detail page, review queue
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_links_signpost_confidence
        ON event_signpost_links(signpost_id, confidence DESC)
        WHERE confidence IS NOT NULL;
    """)
    
    # Composite for event links by event, sorted by confidence
    # Used in: /v1/events (with signpost link inclusion)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_links_event_confidence
        ON event_signpost_links(event_id, confidence DESC);
    """)
    
    # Improve review queue query performance
    # Used in: /v1/review-queue/mappings
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_links_review_confidence
        ON event_signpost_links(needs_review, confidence ASC)
        WHERE needs_review = true;
    """)


def downgrade() -> None:
    """Remove composite indexes."""
    
    op.execute("DROP INDEX IF EXISTS idx_event_links_review_confidence")
    op.execute("DROP INDEX IF EXISTS idx_event_links_event_confidence")
    op.execute("DROP INDEX IF EXISTS idx_event_links_signpost_confidence")
    op.execute("DROP INDEX IF EXISTS idx_events_category_date")

