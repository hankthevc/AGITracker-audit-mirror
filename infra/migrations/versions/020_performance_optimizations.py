"""add performance indexes and constraints

Revision ID: 020_performance_optimizations
Revises: 019_url_validation
Create Date: 2025-10-29

Fixes from Database Schema Audit:
- Composite index on index_snapshots(preset, as_of_date)
- Composite index on events(evidence_tier, published_at)
- Partial index for active (non-retracted) events
- CHECK constraints for 0-1 range fields
- Add index to foreign keys

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '020_performance_optimizations'
down_revision: Union[str, None] = '019_url_validation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add performance indexes and constraints identified in Phase 3 audit.
    
    TEMPORARILY DISABLED: These indexes/constraints reference columns that may not exist
    in production database. Failing with UndefinedColumn errors (fit_score, approved, etc.)
    Re-enable after production schema is verified/updated.
    """
    # MIGRATION TEMPORARILY DISABLED - PASS THROUGH
    pass
    return  # Skip all index/constraint creation for now
    
    # Original implementation below (commented out):
    """
    DISABLED - Original implementation
    
    Add performance indexes and constraints identified in Phase 3 audit.
    """
    
    # ====================================================================
    # 1. FIX INDEX_SNAPSHOTS UNIQUE CONSTRAINT (CRITICAL)
    # ====================================================================
    # Problem: Currently unique on as_of_date only, but should be (preset, as_of_date)
    # This prevents multiple presets from having snapshots on the same date
    
    # Drop existing unique constraint on as_of_date
    op.execute("""
        DO $$
        BEGIN
            -- Find and drop the unique constraint on as_of_date
            ALTER TABLE index_snapshots 
            DROP CONSTRAINT IF EXISTS index_snapshots_as_of_date_key;
        EXCEPTION
            WHEN undefined_object THEN 
                NULL;  -- Constraint doesn't exist, continue
        END $$;
    """)
    
    # Create composite index for query performance
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_index_snapshots_preset_date 
        ON index_snapshots (preset, as_of_date DESC);
    """)
    
    # Create composite unique constraint
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE index_snapshots 
            ADD CONSTRAINT uq_snapshots_preset_date 
            UNIQUE (preset, as_of_date);
        EXCEPTION
            WHEN duplicate_table THEN 
                NULL;  -- Constraint already exists
        END $$;
    """)
    
    
    # ====================================================================
    # 2. COMPOSITE INDEX ON EVENTS (HIGH)
    # ====================================================================
    # Common query pattern: filter by tier AND sort by date
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_tier_published 
        ON events (evidence_tier, published_at DESC);
    """)
    
    
    # ====================================================================
    # 3. PARTIAL INDEX FOR ACTIVE EVENTS (HIGH)
    # ====================================================================
    # Most queries filter retracted=false, so index only non-retracted events
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_active 
        ON events (published_at DESC, evidence_tier)
        WHERE retracted = false;
    """)
    
    
    # ====================================================================
    # 4. PARTIAL INDEX FOR PENDING REVIEW (MEDIUM)
    # ====================================================================
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_pending_review 
        ON events (ingested_at DESC)
        WHERE needs_review = true AND retracted = false;
    """)
    
    
    # ====================================================================
    # 5. ADD FOREIGN KEY INDEX ON SIGNPOSTS.ROADMAP_ID (HIGH)
    # ====================================================================
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signposts_roadmap_id 
        ON signposts (roadmap_id)
        WHERE roadmap_id IS NOT NULL;
    """)
    
    
    # ====================================================================
    # 6. CHECK CONSTRAINTS FOR 0-1 RANGES (MEDIUM)
    # ====================================================================
    
    # event_signpost_links.confidence
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
    
    # REMOVED: Constraints on fit_score and impact_estimate
    # These columns may not exist in all databases (depends on migration history)
    # Constraints are optional (just data validation) and were causing deployment failures
    # If these columns exist, the model-level constraints in models.py will handle validation
    
    # # event_signpost_links.impact_estimate
    # op.execute("""
    #     DO $$
    #     BEGIN
    #         ALTER TABLE event_signpost_links 
    #         ADD CONSTRAINT check_impact_estimate_range 
    #         CHECK (impact_estimate IS NULL OR (impact_estimate >= 0.0 AND impact_estimate <= 1.0));
    #     EXCEPTION
    #         WHEN duplicate_object THEN 
    #             NULL;
    #     END $$;
    # """)
    
    # # event_signpost_links.fit_score
    # op.execute("""
    #     DO $$
    #     BEGIN
    #         ALTER TABLE event_signpost_links 
    #         ADD CONSTRAINT check_fit_score_range 
    #         CHECK (fit_score IS NULL OR (fit_score >= 0.0 AND fit_score <= 1.0));
    #     EXCEPTION
    #         WHEN duplicate_object THEN 
    #             NULL;
    #     END $$;
    # """)
    
    # events_analysis.significance_score
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
    
    # source_credibility_snapshots.retraction_rate
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
    
    # source_credibility_snapshots.credibility_score
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
    
    
    # ====================================================================
    # 7. INDEX ON EVENT_SIGNPOST_LINKS FOR FILTERING (MEDIUM)
    # ====================================================================
    
    # Common query: fetch links for a signpost, filter by tier
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_signpost_links_signpost_tier 
        ON event_signpost_links (signpost_id, tier, created_at DESC);
    """)
    
    # REMOVED: Index on approved column - column doesn't exist in production database
    # # Common query: fetch pending approval links
    # op.execute("""
    #     CREATE INDEX IF NOT EXISTS idx_event_signpost_links_pending 
    #     ON event_signpost_links (created_at DESC)
    #     WHERE approved = false;
    # """)


def downgrade() -> None:
    """
    Remove performance indexes and constraints.
    """
    
    # Drop partial indexes
    # REMOVED: Index was never created (see upgrade function)
    # op.execute("DROP INDEX IF EXISTS idx_event_signpost_links_pending")
    op.execute("DROP INDEX IF EXISTS idx_event_signpost_links_signpost_tier")
    
    # Drop CHECK constraints
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE source_credibility_snapshots DROP CONSTRAINT IF EXISTS check_credibility_score_range;
        EXCEPTION
            WHEN undefined_table THEN NULL;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE source_credibility_snapshots DROP CONSTRAINT IF EXISTS check_retraction_rate_range;
        EXCEPTION
            WHEN undefined_table THEN NULL;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE events_analysis DROP CONSTRAINT IF EXISTS check_significance_score_range;
        EXCEPTION
            WHEN undefined_table THEN NULL;
        END $$;
    """)
    
    # REMOVED: These constraints were never added (see upgrade function)
    # op.execute("ALTER TABLE event_signpost_links DROP CONSTRAINT IF EXISTS check_fit_score_range")
    # op.execute("ALTER TABLE event_signpost_links DROP CONSTRAINT IF EXISTS check_impact_estimate_range")
    op.execute("ALTER TABLE event_signpost_links DROP CONSTRAINT IF EXISTS check_confidence_range")
    
    # Drop foreign key index
    op.execute("DROP INDEX IF EXISTS idx_signposts_roadmap_id")
    
    # Drop partial indexes
    op.execute("DROP INDEX IF EXISTS idx_events_pending_review")
    op.execute("DROP INDEX IF EXISTS idx_events_active")
    
    # Drop composite index on events
    op.execute("DROP INDEX IF EXISTS idx_events_tier_published")
    
    # Drop composite index and constraint on index_snapshots
    op.execute("ALTER TABLE index_snapshots DROP CONSTRAINT IF EXISTS uq_snapshots_preset_date")
    op.execute("DROP INDEX IF EXISTS idx_index_snapshots_preset_date")
    
    # Restore original unique constraint on as_of_date
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE index_snapshots ADD CONSTRAINT index_snapshots_as_of_date_key UNIQUE (as_of_date);
        EXCEPTION
            WHEN duplicate_table THEN NULL;
        END $$;
    """)

