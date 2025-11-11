"""Add composite indexes for query optimization (P0-3)

Revision ID: 20251029_p0_indexes
Revises: 20251029_add_embeddings
Create Date: 2025-10-29

Critical performance fix: Add composite indexes to prevent table scans
on frequently queried columns.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '20251029_p0_indexes'
down_revision = '20251029_add_embeddings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add composite indexes for optimal query performance."""
    
    # Events table: tier + date + retracted (most common query pattern)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_tier_date_retracted 
        ON events (evidence_tier, published_at DESC, retracted)
        WHERE retracted = false;
    """)
    
    # Events table: tier + retracted (for filtering)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_tier_retracted
        ON events (evidence_tier, retracted)
        WHERE retracted = false;
    """)
    
    # Event signpost links: signpost + tier + provisional (for gauges)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_signpost_links_signpost_tier
        ON event_signpost_links (signpost_id, tier, provisional)
        WHERE tier IN ('A', 'B');
    """)
    
    # Expert predictions: signpost + date (for forecasts)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_expert_predictions_signpost_date
        ON expert_predictions (signpost_id, predicted_date);
    """)
    
    # Index snapshots: date (for time series)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_index_snapshots_date
        ON index_snapshots (as_of_date DESC);
    """)
    
    print("✅ Added 5 composite indexes for query optimization")


def downgrade() -> None:
    """Remove composite indexes."""
    
    op.execute("DROP INDEX IF EXISTS idx_events_tier_date_retracted;")
    op.execute("DROP INDEX IF EXISTS idx_events_tier_retracted;")
    op.execute("DROP INDEX IF EXISTS idx_event_signpost_links_signpost_tier;")
    op.execute("DROP INDEX IF EXISTS idx_expert_predictions_signpost_date;")
    op.execute("DROP INDEX IF EXISTS idx_index_snapshots_date;")
    
    print("✅ Removed composite indexes")

