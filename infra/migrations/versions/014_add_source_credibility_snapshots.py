"""Add source_credibility_snapshots table

Revision ID: 014_add_source_credibility_snapshots
Revises: 013_add_llm_prompt_runs
Create Date: 2024-12-19 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014_add_source_credibility_snapshots'
down_revision = '013_add_llm_prompt_runs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create source_credibility_snapshots table
    op.create_table(
        'source_credibility_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('publisher', sa.String(length=255), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('total_articles', sa.Integer(), nullable=False),
        sa.Column('retracted_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('retraction_rate', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('credibility_score', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('credibility_tier', sa.String(length=1), nullable=False),
        sa.Column('methodology', sa.String(length=50), nullable=False, server_default='wilson_95ci_lower'),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_source_cred_publisher', 'source_credibility_snapshots', ['publisher'])
    op.create_index('idx_source_cred_date', 'source_credibility_snapshots', ['snapshot_date'])
    op.create_index('idx_source_cred_publisher_date', 'source_credibility_snapshots', ['publisher', 'snapshot_date'])
    op.create_index('idx_source_cred_tier', 'source_credibility_snapshots', ['credibility_tier'])
    
    # Create unique constraint: one snapshot per publisher per day
    op.create_unique_constraint(
        'uq_source_cred_publisher_date',
        'source_credibility_snapshots',
        ['publisher', 'snapshot_date']
    )


def downgrade() -> None:
    op.drop_constraint('uq_source_cred_publisher_date', 'source_credibility_snapshots', type_='unique')
    op.drop_index('idx_source_cred_tier', table_name='source_credibility_snapshots')
    op.drop_index('idx_source_cred_publisher_date', table_name='source_credibility_snapshots')
    op.drop_index('idx_source_cred_date', table_name='source_credibility_snapshots')
    op.drop_index('idx_source_cred_publisher', table_name='source_credibility_snapshots')
    op.drop_table('source_credibility_snapshots')

