"""Add is_synthetic flag to events table

Revision ID: 010_add_is_synthetic
Revises: 009a_add_link_approved_at
Create Date: 2025-10-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010_add_is_synthetic'
down_revision = '009a_add_link_approved_at'
branch_labels = None
depends_on = None


def upgrade():
    """Add is_synthetic column to events table to mark fixture/test data."""
    op.add_column('events', sa.Column('is_synthetic', sa.Boolean(), server_default='false', nullable=False))
    op.create_index(op.f('ix_events_is_synthetic'), 'events', ['is_synthetic'], unique=False)
    
    # Mark existing events with suspicious patterns as synthetic
    # This helps clean up any existing synthetic data
    op.execute("""
        UPDATE events 
        SET is_synthetic = true 
        WHERE source_url ~ '.*\\.local(/|$)'
           OR source_url ~ '/[a-f0-9]{8,}$'
           OR source_url LIKE '%dev-fixture%'
           OR source_url LIKE '%/test/%'
           OR source_url LIKE '%/synthetic/%'
           OR source_url LIKE '%/fixture/%'
    """)


def downgrade():
    """Remove is_synthetic column."""
    op.drop_index(op.f('ix_events_is_synthetic'), table_name='events')
    op.drop_column('events', 'is_synthetic')
