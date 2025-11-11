"""Add review fields to events and event_signpost_links

Revision ID: 009_add_review_fields
Revises: 008_add_outlet_cred_and_link_type
Create Date: 2024-12-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_add_review_fields'
down_revision = '008_add_outlet_cred_and_link_type'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the review_status enum type
    review_status_enum = postgresql.ENUM('pending', 'approved', 'rejected', 'flagged', name='review_status')
    review_status_enum.create(op.get_bind())
    
    # Add review fields to events table
    op.add_column('events', sa.Column('reviewed_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('events', sa.Column('review_status', review_status_enum, nullable=True))
    op.add_column('events', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('events', sa.Column('flag_reason', sa.Text(), nullable=True))
    
    # Add review fields to event_signpost_links table
    op.add_column('event_signpost_links', sa.Column('needs_review', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('event_signpost_links', sa.Column('reviewed_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('event_signpost_links', sa.Column('review_status', review_status_enum, nullable=True))
    op.add_column('event_signpost_links', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('event_signpost_links', sa.Column('impact_estimate', sa.Numeric(precision=3, scale=2), nullable=True))


def downgrade() -> None:
    # Remove review fields from event_signpost_links table
    op.drop_column('event_signpost_links', 'impact_estimate')
    op.drop_column('event_signpost_links', 'rejection_reason')
    op.drop_column('event_signpost_links', 'review_status')
    op.drop_column('event_signpost_links', 'reviewed_at')
    op.drop_column('event_signpost_links', 'needs_review')
    
    # Remove review fields from events table
    op.drop_column('events', 'flag_reason')
    op.drop_column('events', 'rejection_reason')
    op.drop_column('events', 'review_status')
    op.drop_column('events', 'reviewed_at')
    
    # Drop the review_status enum type
    review_status_enum = postgresql.ENUM('pending', 'approved', 'rejected', 'flagged', name='review_status')
    review_status_enum.drop(op.get_bind())
