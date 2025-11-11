"""add forecasts table for expert predictions

Revision ID: 033_forecasts
Revises: 032_progress_index
Create Date: 2025-11-11

FEATURE: Add forecasts table for tracking expert AGI timeline predictions.

This table stores per-signpost forecasts from various experts and sources
(Aschenbrenner, Cotra/Bioanchors, Epoch AI, etc.) to enable:
- Consensus timeline visualization
- Forecast accuracy tracking over time
- Expert disagreement analysis
- Update history for evolving predictions

Schema:
- source: Expert/org name (e.g., "Aschenbrenner", "Cotra", "Epoch")
- signpost_code: Links to signposts table
- timeline: Predicted achievement date
- confidence: Expert's stated confidence (0.0-1.0)
- quote: Supporting quote/reasoning
- url: Source URL for verification
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '033_forecasts'
down_revision: Union[str, None] = '032_progress_index'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create forecasts table."""
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS forecasts (
            id SERIAL PRIMARY KEY,
            source TEXT NOT NULL,
            signpost_code TEXT NOT NULL,
            timeline DATE NOT NULL,
            confidence NUMERIC(4, 2) CHECK (confidence >= 0 AND confidence <= 1),
            quote TEXT,
            url TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    # Foreign key to signposts table
    op.execute("""
        ALTER TABLE forecasts
        ADD CONSTRAINT fk_forecasts_signpost
        FOREIGN KEY (signpost_code)
        REFERENCES signposts(code)
        ON DELETE CASCADE
    """)
    
    # Index for querying forecasts by signpost
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_forecasts_signpost_timeline
        ON forecasts(signpost_code, timeline DESC)
    """)
    
    # Index for querying by source (expert)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_forecasts_source
        ON forecasts(source)
    """)
    
    # Index for date range queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_forecasts_timeline
        ON forecasts(timeline)
    """)
    
    print("✓ Created forecasts table")
    print("✓ Added foreign key to signposts")
    print("✓ Added indexes for signpost_code, source, and timeline")


def downgrade() -> None:
    """Drop forecasts table."""
    
    op.execute("DROP TABLE IF EXISTS forecasts CASCADE")
    
    print("✓ Dropped forecasts table")

