"""add dashboard_snapshots table

Revision ID: 031_dashboard_snaps
Revises: 030_openai_prep_conf
Create Date: 2025-11-07

FEATURE: Add dashboard_snapshots table for caching homepage data.

This table stores daily homepage snapshots (KPIs, featured charts, news, analysis)
to provide fast, consistent data for the FiveThirtyEight-style homepage.

Benefits:
- Faster page loads (pre-computed data)
- Consistent view within 24h window
- Reduces database load
- Enables A/B testing of analysis text
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers
revision: str = '031_dashboard_snaps'
down_revision: Union[str, None] = '030_openai_prep_conf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create dashboard_snapshots table."""
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_snapshots (
            id SERIAL PRIMARY KEY,
            generated_at TIMESTAMPTZ NOT NULL UNIQUE,
            snapshot JSONB NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    # Index for fast lookup of latest snapshot
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_dashboard_snapshots_generated_at
        ON dashboard_snapshots(generated_at DESC)
    """)
    
    print("✓ Created dashboard_snapshots table")
    print("✓ Added index on generated_at")


def downgrade() -> None:
    """Drop dashboard_snapshots table."""
    
    op.execute("DROP TABLE IF EXISTS dashboard_snapshots CASCADE")
    
    print("✓ Dropped dashboard_snapshots table")

