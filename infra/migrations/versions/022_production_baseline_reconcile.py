"""production baseline - reconcile schema with models

Revision ID: 022_production_baseline
Revises: 20251029_p1_audit_log
Create Date: 2025-10-31

This migration reconciles the production database schema with models.py by:
1. Removing placeholder embedding columns (Phase 6 RAG deferred)
2. Re-enabling safe indexes from disabled migrations 018/020
3. Documenting production baseline state
4. Ensuring schema matches models.py exactly

Context:
- Migrations 018, 020, 20251029_add_embeddings were DISABLED (pass-through)
- Embedding columns commented out in models.py (Phase 6 not ready)
- impact_estimate, fit_score, approved columns commented out (not in production)
- This migration establishes a clean baseline for production deployment
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '022_production_baseline'
down_revision: Union[str, None] = '20251029_p1_audit_log'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Reconcile production schema with models.py.
    
    This migration is IDEMPOTENT and safe to run multiple times.
    It uses IF EXISTS / IF NOT EXISTS for all operations.
    """
    
    # ====================================================================
    # 1. CLEANUP: Remove embedding columns (Phase 6 deferred)
    # ====================================================================
    # These columns were never fully deployed. Models.py has them commented out.
    # Phase 6 (RAG/vector search) is deferred until proper pgvector setup.
    
    op.execute("""
        -- Drop embedding columns from events table if they exist
        DO $$
        BEGIN
            ALTER TABLE events DROP COLUMN IF EXISTS embedding;
        EXCEPTION
            WHEN undefined_column THEN
                NULL;  -- Column doesn't exist, continue
        END $$;
    """)
    
    op.execute("""
        -- Drop embedding columns from signposts table if they exist
        DO $$
        BEGIN
            ALTER TABLE signposts DROP COLUMN IF EXISTS embedding;
        EXCEPTION
            WHEN undefined_column THEN
                NULL;  -- Column doesn't exist, continue
        END $$;
    """)
    
    # ====================================================================
    # 2. RE-ENABLE SAFE INDEXES from migration 018 (events table)
    # ====================================================================
    # These indexes are safe and don't reference non-existent columns
    
    # Composite index for filtering by tier and ordering by date
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_tier_published 
        ON events(evidence_tier, published_at DESC);
    """)
    
    # Composite index for filtering by retraction status and date
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_retracted_published 
        ON events(retracted, published_at DESC);
    """)
    
    # Composite index for filtering by provisional status and date  
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_provisional_published 
        ON events(provisional, published_at DESC);
    """)
    
    # Index for cursor-based pagination
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_published_id 
        ON events(published_at DESC, id DESC);
    """)
    
    # Full-text search index on title
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_title_fts 
        ON events USING gin(to_tsvector('english', title));
    """)
    
    # Full-text search index on summary (with COALESCE for nullable column)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_summary_fts 
        ON events USING gin(to_tsvector('english', COALESCE(summary, '')));
    """)
    
    # ====================================================================
    # 3. RE-ENABLE SAFE INDEXES from migration 018 (other tables)
    # ====================================================================
    
    # event_signpost_links: Composite index on tier + confidence
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_signpost_tier_confidence 
        ON event_signpost_links(tier, confidence DESC) 
        WHERE tier IS NOT NULL;
    """)
    
    # event_signpost_links: Index on created_at
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_signpost_created 
        ON event_signpost_links(created_at DESC);
    """)
    
    # event_signpost_links: Composite index for signpost + event lookups
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_signpost_signpost_event 
        ON event_signpost_links(signpost_id, event_id);
    """)
    
    # events_analysis: Composite index for event analysis lookups
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_analysis_event_generated 
        ON events_analysis(event_id, generated_at DESC);
    """)
    
    # sources: Index on domain
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_sources_domain 
        ON sources(domain);
    """)
    
    # signposts: Index on category
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signposts_category 
        ON signposts(category);
    """)
    
    # ====================================================================
    # 4. RE-ENABLE SAFE INDEXES from migration 020
    # ====================================================================
    
    # index_snapshots: Composite index on preset + date
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_index_snapshots_preset_date 
        ON index_snapshots(preset, as_of_date DESC);
    """)
    
    # Fix index_snapshots unique constraint (preset, as_of_date)
    op.execute("""
        DO $$
        BEGIN
            -- Drop old unique constraint on as_of_date only
            ALTER TABLE index_snapshots 
            DROP CONSTRAINT IF EXISTS index_snapshots_as_of_date_key;
        EXCEPTION
            WHEN undefined_object THEN 
                NULL;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            -- Create composite unique constraint
            ALTER TABLE index_snapshots 
            ADD CONSTRAINT uq_snapshots_preset_date 
            UNIQUE (preset, as_of_date);
        EXCEPTION
            WHEN duplicate_table THEN 
                NULL;  -- Constraint already exists
        END $$;
    """)
    
    # events: Partial index for active (non-retracted) events
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_active 
        ON events(published_at DESC, evidence_tier)
        WHERE retracted = false;
    """)
    
    # events: Partial index for pending review
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_pending_review 
        ON events(ingested_at DESC)
        WHERE needs_review = true AND retracted = false;
    """)
    
    # signposts: Index on roadmap_id (foreign key)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signposts_roadmap_id 
        ON signposts(roadmap_id)
        WHERE roadmap_id IS NOT NULL;
    """)
    
    # event_signpost_links: Composite index for filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_signpost_links_signpost_tier 
        ON event_signpost_links(signpost_id, tier, created_at DESC);
    """)
    
    # ====================================================================
    # 5. CHECK CONSTRAINTS for 0-1 range validation
    # ====================================================================
    
    # event_signpost_links.confidence (0.00 to 1.00)
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE event_signpost_links 
            ADD CONSTRAINT check_confidence_range 
            CHECK (confidence >= 0.00 AND confidence <= 1.00);
        EXCEPTION
            WHEN duplicate_object THEN 
                NULL;  -- Constraint already exists
        END $$;
    """)
    
    # events_analysis.significance_score (0.0 to 1.0)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'events_analysis'
            ) THEN
                ALTER TABLE events_analysis 
                ADD CONSTRAINT check_significance_score_range 
                CHECK (significance_score IS NULL OR (significance_score >= 0.0 AND significance_score <= 1.0));
            END IF;
        EXCEPTION
            WHEN duplicate_object THEN 
                NULL;
        END $$;
    """)
    
    # source_credibility_snapshots.retraction_rate (0.0 to 1.0)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'source_credibility_snapshots'
            ) THEN
                ALTER TABLE source_credibility_snapshots 
                ADD CONSTRAINT check_retraction_rate_range 
                CHECK (retraction_rate >= 0.0 AND retraction_rate <= 1.0);
            END IF;
        EXCEPTION
            WHEN duplicate_object THEN 
                NULL;
        END $$;
    """)
    
    # source_credibility_snapshots.credibility_score (0.0 to 1.0)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'source_credibility_snapshots'
            ) THEN
                ALTER TABLE source_credibility_snapshots 
                ADD CONSTRAINT check_credibility_score_range 
                CHECK (credibility_score >= 0.0 AND credibility_score <= 1.0);
            END IF;
        EXCEPTION
            WHEN duplicate_object THEN 
                NULL;
        END $$;
    """)


def downgrade() -> None:
    """
    Rollback production baseline changes.
    
    Warning: This will drop performance indexes and constraints.
    """
    
    # Drop CHECK constraints
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE source_credibility_snapshots 
            DROP CONSTRAINT IF EXISTS check_credibility_score_range;
        EXCEPTION
            WHEN undefined_table THEN NULL;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE source_credibility_snapshots 
            DROP CONSTRAINT IF EXISTS check_retraction_rate_range;
        EXCEPTION
            WHEN undefined_table THEN NULL;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE events_analysis 
            DROP CONSTRAINT IF EXISTS check_significance_score_range;
        EXCEPTION
            WHEN undefined_table THEN NULL;
        END $$;
    """)
    
    op.execute("ALTER TABLE event_signpost_links DROP CONSTRAINT IF EXISTS check_confidence_range")
    
    # Drop indexes
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_event_signpost_links_signpost_tier")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_signposts_roadmap_id")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_events_pending_review")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_events_active")
    
    # Restore old unique constraint and drop new one
    op.execute("ALTER TABLE index_snapshots DROP CONSTRAINT IF EXISTS uq_snapshots_preset_date")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_index_snapshots_preset_date")
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE index_snapshots 
            ADD CONSTRAINT index_snapshots_as_of_date_key UNIQUE (as_of_date);
        EXCEPTION
            WHEN duplicate_table THEN NULL;
        END $$;
    """)
    
    # Drop indexes from migration 020
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_signposts_category")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_sources_domain")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_events_analysis_event_generated")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_event_signpost_signpost_event")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_event_signpost_created")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_event_signpost_tier_confidence")
    
    # Drop indexes from migration 018
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_events_summary_fts")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_events_title_fts")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_events_published_id")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_events_provisional_published")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_events_retracted_published")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_events_tier_published")
    
    # Note: We do NOT re-add embedding columns in downgrade
    # Phase 6 is not ready, and these columns should not exist in production

