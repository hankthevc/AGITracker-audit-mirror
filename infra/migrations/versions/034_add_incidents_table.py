"""add incidents table for safety tracking

Revision ID: 034_incidents
Revises: 033_forecasts
Create Date: 2025-11-11

FEATURE: Add incidents table for tracking AI safety incidents, jailbreaks, and misuses.

This table stores notable incidents to overlay on charts and enable filtering by:
- Severity level (1-5: info, low, medium, high, critical)
- Incident vectors (jailbreak, misuse, bias, privacy, etc.)
- Related signposts (to show context)
- Date occurrence for timeline visualization

Use cases:
- Timeline annotation (show incidents on progress charts)
- Trend analysis (incidents per month, severity over time)
- Signpost correlation (which areas have most incidents)
- Export for research (CSV with citations)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers
revision: str = '034_incidents'
down_revision: Union[str, None] = '033_forecasts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create incidents table."""
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id SERIAL PRIMARY KEY,
            occurred_at DATE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            severity INTEGER NOT NULL CHECK (severity >= 1 AND severity <= 5),
            vectors TEXT[],
            signpost_codes TEXT[],
            external_url TEXT,
            source TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    # Index for timeline queries (most common)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_occurred_at
        ON incidents(occurred_at DESC)
    """)
    
    # Index for severity filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_severity
        ON incidents(severity)
    """)
    
    # GIN index for array containment queries (vectors and signpost_codes)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_vectors_gin
        ON incidents USING GIN(vectors)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_signpost_codes_gin
        ON incidents USING GIN(signpost_codes)
    """)
    
    print("✓ Created incidents table")
    print("✓ Added indexes for occurred_at, severity, vectors, signpost_codes")


def downgrade() -> None:
    """Drop incidents table."""
    
    op.execute("DROP TABLE IF EXISTS incidents CASCADE")
    
    print("✓ Dropped incidents table")

