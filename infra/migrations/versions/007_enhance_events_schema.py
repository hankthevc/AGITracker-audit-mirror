"""enhance events schema with source_type, content fields, and ingest_runs

Revision ID: 007_enhance_events
Revises: 6e2841a56cb2
Create Date: 2025-10-15 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007_enhance_events'
down_revision: Union[str, None] = '6e2841a56cb2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add source_type enum
    source_type_enum = sa.Enum('news', 'paper', 'blog', 'leaderboard', 'gov', name='source_type')
    source_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Add new columns to events table
    op.add_column('events', sa.Column('source_type', source_type_enum, nullable=True))
    op.add_column('events', sa.Column('source_domain', sa.String(255), nullable=True))
    op.add_column('events', sa.Column('content_text', sa.Text(), nullable=True))
    op.add_column('events', sa.Column('author', sa.String(255), nullable=True))
    op.add_column('events', sa.Column('byline', sa.String(500), nullable=True))
    op.add_column('events', sa.Column('lang', sa.String(10), nullable=True, server_default='en'))
    op.add_column('events', sa.Column('retracted', sa.Boolean(), nullable=False, server_default='false'))
    
    # Set source_type based on evidence_tier as initial migration
    # A = paper/leaderboard, B = blog, C/D = news
    op.execute("""
        UPDATE events 
        SET source_type = CASE 
            WHEN evidence_tier = 'A' THEN 'paper'::source_type
            WHEN evidence_tier = 'B' THEN 'blog'::source_type
            ELSE 'news'::source_type
        END
        WHERE source_type IS NULL
    """)
    
    # Now make source_type non-nullable
    op.alter_column('events', 'source_type', nullable=False)
    
    # Extract domain from source_url
    op.execute("""
        UPDATE events 
        SET source_domain = CASE
            WHEN source_url LIKE '%://%.%' THEN 
                SUBSTRING(source_url FROM '://([^/]+)')
            ELSE NULL
        END
        WHERE source_domain IS NULL
    """)
    
    # Create index on source_type
    op.create_index('idx_events_source_type', 'events', ['source_type'])
    
    # Create ingest_runs table
    op.create_table(
        'ingest_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connector_name', sa.String(100), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('success', 'fail', 'running', name='ingest_status'), nullable=False),
        sa.Column('new_events_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('new_links_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes on ingest_runs
    op.create_index('idx_ingest_runs_connector', 'ingest_runs', ['connector_name'])
    op.create_index('idx_ingest_runs_started', 'ingest_runs', ['started_at'], postgresql_ops={'started_at': 'DESC'})
    op.create_index('idx_ingest_runs_status', 'ingest_runs', ['status'])


def downgrade() -> None:
    # Drop ingest_runs table
    op.drop_index('idx_ingest_runs_status', table_name='ingest_runs')
    op.drop_index('idx_ingest_runs_started', table_name='ingest_runs')
    op.drop_index('idx_ingest_runs_connector', table_name='ingest_runs')
    op.drop_table('ingest_runs')
    op.execute('DROP TYPE ingest_status')
    
    # Drop indexes and columns from events
    op.drop_index('idx_events_source_type', table_name='events')
    op.drop_column('events', 'retracted')
    op.drop_column('events', 'lang')
    op.drop_column('events', 'byline')
    op.drop_column('events', 'author')
    op.drop_column('events', 'content_text')
    op.drop_column('events', 'source_domain')
    op.drop_column('events', 'source_type')
    
    # Drop source_type enum
    op.execute('DROP TYPE source_type')

