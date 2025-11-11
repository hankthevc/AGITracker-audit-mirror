"""Add retraction tracking fields to events

Revision ID: 011_add_retraction_fields
Revises: 009_add_review_fields
Create Date: 2024-12-19 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011_add_retraction_fields'
down_revision = '009_add_review_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add retraction tracking fields to events table (idempotent)
    # Use raw SQL with IF NOT EXISTS for idempotency
    op.execute("""
        ALTER TABLE events 
        ADD COLUMN IF NOT EXISTS retracted_at TIMESTAMPTZ;
    """)
    op.execute("""
        ALTER TABLE events 
        ADD COLUMN IF NOT EXISTS retraction_reason TEXT;
    """)
    op.execute("""
        ALTER TABLE events 
        ADD COLUMN IF NOT EXISTS retraction_evidence_url TEXT;
    """)
    
    # Create index if not exists (partial index for efficiency)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_events_retracted_at 
        ON events(retracted_at) 
        WHERE retracted_at IS NOT NULL;
    """)
    
    # Add index on retracted column if it doesn't exist
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_retracted 
        ON events(retracted);
    """)


def downgrade() -> None:
    # Remove retraction tracking fields
    op.drop_column('events', 'retraction_evidence_url')
    op.drop_column('events', 'retraction_reason')
    op.drop_column('events', 'retracted_at')
    
    # Drop index
    try:
        op.drop_index('idx_events_retracted', table_name='events')
    except:
        pass
