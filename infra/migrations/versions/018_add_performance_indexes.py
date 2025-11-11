"""add performance indexes for Sprint 9

Revision ID: 018_performance_indexes
Revises: 017_enhance_api_keys
Create Date: 2025-10-29 00:00:00.000000

Adds composite indexes and full-text search indexes for optimal query performance
with 10,000+ events. Targets <100ms P95 response times.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '018_performance_indexes'
down_revision: Union[str, None] = '017_enhance_api_keys'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add performance indexes for Sprint 9 optimization.
    
    TEMPORARILY DISABLED: These indexes reference columns that may not exist
    in all production databases. Migrations were failing with UndefinedColumn errors.
    Re-enable after verifying production schema matches models.py
    """
    # MIGRATION TEMPORARILY DISABLED - PASS THROUGH
    pass
    return  # Skip all index creation for now
    
    # Original implementation below (commented out):
    """
    Original implementation - DISABLED
    
    Add performance indexes for Sprint 9 optimization.
    
    Strategy:
    - Composite indexes for common query patterns (tier + published_at)
    - Full-text search indexes (GIN) for Sprint 10 preparation
    - Indexes on foreign keys and commonly filtered columns
    
    All queries target P95 < 100ms for 10,000+ events.
    """
    
    # ======================================================================
    # EVENTS TABLE INDEXES
    # ======================================================================
    
    # Composite index for filtering by tier and ordering by date (most common query)
    # Supports: WHERE evidence_tier = 'A' ORDER BY published_at DESC
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_tier_published 
            ON events(evidence_tier, published_at DESC);
        """)
    
    # Composite index for filtering by retraction status and date
    # Supports: WHERE retracted = FALSE ORDER BY published_at DESC
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_retracted_published 
            ON events(retracted, published_at DESC);
        """)
    
    # Composite index for filtering by provisional status and date
    # Supports: WHERE provisional = FALSE ORDER BY published_at DESC
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_provisional_published 
            ON events(provisional, published_at DESC);
        """)
    
    # Index for cursor-based pagination (composite on published_at + id)
    # Supports: WHERE (published_at, id) < (cursor_time, cursor_id)
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_published_id 
            ON events(published_at DESC, id DESC);
        """)
    
    # Full-text search indexes (GIN) for Sprint 10
    # Note: Uses 'english' text search configuration
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_title_fts 
            ON events USING gin(to_tsvector('english', title));
        """)
    
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_summary_fts 
            ON events USING gin(to_tsvector('english', COALESCE(summary, '')));
        """)
    
    # ======================================================================
    # EVENT_SIGNPOST_LINKS TABLE INDEXES
    # ======================================================================
    
    # Composite index on tier + confidence for filtering high-confidence links
    # Supports: WHERE tier = 'A' ORDER BY confidence DESC
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_signpost_tier_confidence 
            ON event_signpost_links(tier, confidence DESC) 
            WHERE tier IS NOT NULL;
        """)
    
    # Index on created_at for temporal queries
    # Supports: ORDER BY created_at DESC (for recent mappings)
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_signpost_created 
            ON event_signpost_links(created_at DESC);
        """)
    
    # Composite index for signpost + event lookups
    # Supports: WHERE signpost_id = X AND event_id IN (...)
    # Note: (signpost_id, event_id) already has unique constraint from earlier migration
    # This index provides additional query optimization
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_signpost_signpost_event 
            ON event_signpost_links(signpost_id, event_id);
        """)
    
    # ======================================================================
    # EVENTS_ANALYSIS TABLE INDEXES
    # ======================================================================
    
    # Composite index for event analysis lookups
    # Supports: WHERE event_id = X ORDER BY generated_at DESC
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_analysis_event_generated 
            ON events_analysis(event_id, generated_at DESC);
        """)
    
    # REMOVED: Index on analysis_content - column doesn't exist
    # The events_analysis table doesn't have an analysis_content column
    # If this column is added in a future migration, add this index then
    
    # ======================================================================
    # SOURCES TABLE INDEXES
    # ======================================================================
    
    # Index on source domain for lookups
    # Supports: WHERE domain = 'arxiv.org'
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_sources_domain 
            ON sources(domain);
        """)
    
    # ======================================================================
    # SIGNPOSTS TABLE INDEXES
    # ======================================================================
    
    # Index on category for grouping queries
    # Supports: WHERE category = 'capabilities'
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_signposts_category 
            ON signposts(category);
        """)


def downgrade() -> None:
    """
    Remove Sprint 9 performance indexes.
    """
    # Drop all indexes in reverse order
    op.execute("DROP INDEX IF EXISTS idx_signposts_category")
    op.execute("DROP INDEX IF EXISTS idx_sources_domain")
    op.execute("DROP INDEX IF EXISTS idx_events_analysis_content_fts")
    op.execute("DROP INDEX IF EXISTS idx_events_analysis_event_generated")
    op.execute("DROP INDEX IF EXISTS idx_event_signpost_signpost_event")
    op.execute("DROP INDEX IF EXISTS idx_event_signpost_created")
    op.execute("DROP INDEX IF EXISTS idx_event_signpost_tier_confidence")
    op.execute("DROP INDEX IF EXISTS idx_events_summary_fts")
    op.execute("DROP INDEX IF EXISTS idx_events_title_fts")
    op.execute("DROP INDEX IF EXISTS idx_events_published_id")
    op.execute("DROP INDEX IF EXISTS idx_events_provisional_published")
    op.execute("DROP INDEX IF EXISTS idx_events_retracted_published")
    op.execute("DROP INDEX IF EXISTS idx_events_tier_published")
