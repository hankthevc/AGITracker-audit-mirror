"""Phase 1 events analysis: LLM-generated event summaries

Revision ID: 20251020115050
Revises: 20251020115049
Create Date: 2025-10-20 11:50:50.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '20251020115050'
down_revision: Union[str, None] = '20251020115049'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create events_analysis table for LLM-generated analysis
    op.create_table(
        'events_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('relevance_explanation', sa.Text(), nullable=True),
        sa.Column('impact_json', JSONB, nullable=True),
        sa.Column('confidence_reasoning', sa.Text(), nullable=True),
        sa.Column('significance_score', sa.Float(), nullable=True),
        sa.Column('llm_version', sa.String(100), nullable=True),
        sa.Column('generated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for efficient lookups (event_id, generated_at DESC)
    op.create_index(
        'idx_events_analysis_event_generated',
        'events_analysis',
        ['event_id', sa.text('generated_at DESC')],
        postgresql_ops={'generated_at': 'DESC'}
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_events_analysis_event_generated', table_name='events_analysis')
    
    # Drop table
    op.drop_table('events_analysis')

