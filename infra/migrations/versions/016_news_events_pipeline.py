"""news events pipeline enhancements: dedup_hash, tier, provisional

Revision ID: 016_news_pipeline
Revises: 20251020115051
Create Date: 2025-10-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '016_news_pipeline'
down_revision: Union[str, None] = '015_merge_branches'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add missing columns for Phase A news events pipeline.
    
    Uses IF NOT EXISTS pattern for idempotency where possible.
    """
    
    # ======================================================================
    # EVENTS TABLE ENHANCEMENTS
    # ======================================================================
    
    # Add dedup_hash column to events for robust deduplication
    # This will be computed from: normalized_title + source_domain + published_date
    with op.get_context().autocommit_block():
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'events' AND column_name = 'dedup_hash'
                ) THEN
                    ALTER TABLE events ADD COLUMN dedup_hash TEXT NULL;
                END IF;
            END $$;
        """)
    
    # Create unique index on dedup_hash (where not null)
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_events_dedup_hash 
            ON events(dedup_hash) 
            WHERE dedup_hash IS NOT NULL;
        """)
    
    # Ensure ingested_at exists (may already be there from migration 6e2841a56cb2)
    with op.get_context().autocommit_block():
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'events' AND column_name = 'ingested_at'
                ) THEN
                    ALTER TABLE events 
                    ADD COLUMN ingested_at TIMESTAMPTZ DEFAULT NOW() NOT NULL;
                END IF;
            END $$;
        """)
    
    # ======================================================================
    # EVENT_SIGNPOST_LINKS TABLE ENHANCEMENTS
    # ======================================================================
    
    # Add tier column (denormalized from events.outlet_cred for efficient filtering)
    # Use same enum as outlet_cred
    with op.get_context().autocommit_block():
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'event_signpost_links' AND column_name = 'tier'
                ) THEN
                    ALTER TABLE event_signpost_links 
                    ADD COLUMN tier outlet_cred NULL;
                END IF;
            END $$;
        """)
    
    # Backfill tier from events.outlet_cred
    op.execute("""
        UPDATE event_signpost_links esl
        SET tier = e.outlet_cred
        FROM events e
        WHERE esl.event_id = e.id
        AND esl.tier IS NULL;
    """)
    
    # Add provisional column to event_signpost_links
    # C/D tier always provisional, B tier provisional initially (needs A corroboration)
    with op.get_context().autocommit_block():
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'event_signpost_links' AND column_name = 'provisional'
                ) THEN
                    ALTER TABLE event_signpost_links 
                    ADD COLUMN provisional BOOLEAN DEFAULT TRUE NOT NULL;
                END IF;
            END $$;
        """)
    
    # Backfill provisional based on tier:
    # - A tier: provisional = false (direct evidence)
    # - B tier: provisional = true (needs corroboration)
    # - C/D tier: provisional = true (always provisional, never moves gauges)
    op.execute("""
        UPDATE event_signpost_links
        SET provisional = CASE
            WHEN tier = 'A' THEN FALSE
            ELSE TRUE
        END
        WHERE provisional IS NULL;
    """)
    
    # ======================================================================
    # INDEXES
    # ======================================================================
    
    # Index on event_signpost_links(signpost_id, tier) for filtering by tier
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_signpost_links_signpost_tier 
            ON event_signpost_links(signpost_id, tier);
        """)
    
    # Index on event_signpost_links(provisional) for finding provisional links
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_signpost_links_provisional 
            ON event_signpost_links(provisional) 
            WHERE provisional = TRUE;
        """)


def downgrade() -> None:
    """
    Remove Phase A enhancements.
    """
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_event_signpost_links_provisional")
    op.execute("DROP INDEX IF EXISTS idx_event_signpost_links_signpost_tier")
    op.execute("DROP INDEX IF EXISTS idx_events_dedup_hash")
    
    # Drop columns
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'event_signpost_links' AND column_name = 'provisional'
            ) THEN
                ALTER TABLE event_signpost_links DROP COLUMN provisional;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'event_signpost_links' AND column_name = 'tier'
            ) THEN
                ALTER TABLE event_signpost_links DROP COLUMN tier;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'events' AND column_name = 'dedup_hash'
            ) THEN
                ALTER TABLE events DROP COLUMN dedup_hash;
            END IF;
        END $$;
    """)
