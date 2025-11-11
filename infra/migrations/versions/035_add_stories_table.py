"""add stories table for weekly narratives

Revision ID: 035_stories
Revises: 034_incidents
Create Date: 2025-11-11

FEATURE: Add stories table for auto-generated weekly AGI progress narratives.

This table stores weekly "This Week in AGI" stories that summarize:
- Progress index deltas
- Top 3 rising/falling signposts
- Notable incidents
- New forecast updates
- Key events (A/B tier)

Stories are auto-generated and provide narrative context for the numbers.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '035_stories'
down_revision: Union[str, None] = '034_incidents'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create stories table."""
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS stories (
            id SERIAL PRIMARY KEY,
            week_start DATE NOT NULL UNIQUE,
            week_end DATE NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            summary TEXT,
            index_delta NUMERIC(5, 2),
            top_movers JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    # Index for chronological queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_stories_week_start
        ON stories(week_start DESC)
    """)
    
    print("✓ Created stories table")
    print("✓ Added index on week_start DESC")


def downgrade() -> None:
    """Drop stories table."""
    
    op.execute("DROP TABLE IF EXISTS stories CASCADE")
    
    print("✓ Dropped stories table")

