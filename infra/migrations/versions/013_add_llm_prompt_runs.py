"""Add llm_prompt_runs table for LLM call tracking

Revision ID: 013_add_llm_prompt_runs
Revises: 012_add_llm_prompts_table
Create Date: 2024-12-19 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '013_add_llm_prompt_runs'
down_revision = '012_add_llm_prompts_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create llm_prompt_runs table
    op.create_table(
        'llm_prompt_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prompt_id', sa.Integer(), nullable=True),
        sa.Column('task_name', sa.String(length=100), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('input_hash', sa.String(length=64), nullable=False),
        sa.Column('output_hash', sa.String(length=64), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost_usd', sa.Numeric(precision=10, scale=6), nullable=False, server_default='0'),
        sa.Column('model', sa.String(length=50), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['prompt_id'], ['llm_prompts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_llm_prompt_runs_prompt', 'llm_prompt_runs', ['prompt_id'])
    op.create_index('idx_llm_prompt_runs_task', 'llm_prompt_runs', ['task_name'])
    op.create_index('idx_llm_prompt_runs_event', 'llm_prompt_runs', ['event_id'])
    op.create_index('idx_llm_prompt_runs_task_created', 'llm_prompt_runs', ['task_name', 'created_at'])
    op.create_index('idx_llm_prompt_runs_created', 'llm_prompt_runs', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_llm_prompt_runs_created', table_name='llm_prompt_runs')
    op.drop_index('idx_llm_prompt_runs_task_created', table_name='llm_prompt_runs')
    op.drop_index('idx_llm_prompt_runs_event', table_name='llm_prompt_runs')
    op.drop_index('idx_llm_prompt_runs_task', table_name='llm_prompt_runs')
    op.drop_index('idx_llm_prompt_runs_prompt', table_name='llm_prompt_runs')
    op.drop_table('llm_prompt_runs')

