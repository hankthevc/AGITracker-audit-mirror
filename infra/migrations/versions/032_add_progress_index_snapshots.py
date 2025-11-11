"""add progress_index_snapshots table

Revision ID: 032_progress_index
Revises: 031_dashboard_snaps
Create Date: 2025-11-07

FEATURE: Add progress_index_snapshots table for composite AGI progress gauge.

This table stores daily snapshots of the composite progress index that combines
all signpost dimensions (capabilities, agents, inputs, security, economic, research,
geopolitical, safety) into a single explainable topline metric.

Benefits:
- Single number answer to "How close are we to AGI?"
- Historical tracking (trending up/down)
- Component breakdown (which areas are progressing fastest)
- Configurable weights (compare different expert perspectives)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers
revision: str = '032_progress_index'
down_revision: Union[str, None] = '031_dashboard_snaps'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create progress_index_snapshots table."""
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS progress_index_snapshots (
            id SERIAL PRIMARY KEY,
            snapshot_date DATE NOT NULL UNIQUE,
            value NUMERIC(6, 2) NOT NULL CHECK (value >= 0 AND value <= 100),
            components JSONB NOT NULL,
            weights JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    # Index for fast lookup of recent snapshots
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_progress_index_date_desc
        ON progress_index_snapshots(snapshot_date DESC)
    """)
    
    print("✓ Created progress_index_snapshots table")
    print("✓ Added index on snapshot_date DESC")


def downgrade() -> None:
    """Drop progress_index_snapshots table."""
    
    op.execute("DROP TABLE IF EXISTS progress_index_snapshots CASCADE")
    
    print("✓ Dropped progress_index_snapshots table")

