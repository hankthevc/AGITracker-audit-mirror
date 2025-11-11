"""add events and event_signpost_links tables

Revision ID: 6e2841a56cb2
Revises: 004_roadmap_predictions
Create Date: 2025-10-15 15:32:31.338226

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e2841a56cb2'
down_revision: Union[str, None] = '004_roadmap_predictions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create events table (enum will be created automatically)
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('publisher', sa.String(255), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('evidence_tier', sa.Enum('A', 'B', 'C', 'D', name='evidence_tier'), nullable=False),
        sa.Column('provisional', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('parsed', sa.JSON(), nullable=True),
        sa.Column('needs_review', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes on events
    op.create_index('idx_events_published_at', 'events', ['published_at'], postgresql_ops={'published_at': 'DESC'})
    op.create_index('idx_events_publisher', 'events', ['publisher'])
    op.create_index('idx_events_evidence_tier', 'events', ['evidence_tier'])
    op.create_index('idx_events_needs_review', 'events', ['needs_review'])
    
    # Create event_signpost_links table
    op.create_table(
        'event_signpost_links',
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('signpost_id', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('value', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['signpost_id'], ['signposts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('event_id', 'signpost_id')
    )
    
    # Create index on event_signpost_links
    op.create_index('idx_event_signpost_signpost_observed', 'event_signpost_links', 
                    ['signpost_id', 'observed_at'], 
                    postgresql_ops={'observed_at': 'DESC'})
    
    # Create event_entities helper table (optional)
    op.create_table(
        'event_entities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on event_entities
    op.create_index('idx_event_entities_event_id', 'event_entities', ['event_id'])


def downgrade() -> None:
    op.drop_index('idx_event_entities_event_id', table_name='event_entities')
    op.drop_table('event_entities')
    
    op.drop_index('idx_event_signpost_signpost_observed', table_name='event_signpost_links')
    op.drop_table('event_signpost_links')
    
    op.drop_index('idx_events_needs_review', table_name='events')
    op.drop_index('idx_events_evidence_tier', table_name='events')
    op.drop_index('idx_events_publisher', table_name='events')
    op.drop_index('idx_events_published_at', table_name='events')
    op.drop_table('events')
    
    op.execute('DROP TYPE evidence_tier')

