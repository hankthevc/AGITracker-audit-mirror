"""Phase 0 foundations: constraints, indexes, content_hash

Revision ID: 20251020115049
Revises: 010_add_is_synthetic_to_events
Create Date: 2025-10-20 11:50:49.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251020115049'
down_revision: Union[str, None] = '010_add_is_synthetic'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add content_hash column to events for deduplication
    op.add_column('events', sa.Column('content_hash', sa.Text(), nullable=True))
    
    # Add created_at column to event_signpost_links for tracking
    op.add_column(
        'event_signpost_links',
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    
    # Add unique constraint on event_signpost_links (event_id, signpost_id)
    # This prevents duplicate links between the same event and signpost
    op.create_unique_constraint(
        'uq_event_signpost_links_event_signpost',
        'event_signpost_links',
        ['event_id', 'signpost_id']
    )
    
    # Add index on event_signpost_links(signpost_id, created_at) for efficient lookups
    op.create_index(
        'idx_event_signpost_signpost_created',
        'event_signpost_links',
        ['signpost_id', sa.text('created_at DESC')],
        postgresql_ops={'created_at': 'DESC'}
    )
    
    # Note: UNIQUE(signposts.code) already exists in models.py line 54
    # Note: UNIQUE(events.source_url) already exists in models.py line 359
    # Note: events(published_at) index already exists in models.py line 363
    # Note: events(source_type) index already exists in migration 007


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_event_signpost_signpost_created', table_name='event_signpost_links')
    
    # Drop unique constraint
    op.drop_constraint('uq_event_signpost_links_event_signpost', 'event_signpost_links', type_='unique')
    
    # Drop columns
    op.drop_column('event_signpost_links', 'created_at')
    op.drop_column('events', 'content_hash')

