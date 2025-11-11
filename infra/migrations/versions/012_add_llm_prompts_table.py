"""Add LLM prompts table for audit trail

Revision ID: 012_add_llm_prompts_table
Revises: 011_add_retraction_fields
Create Date: 2024-12-19 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012_add_llm_prompts_table'
down_revision = '011_add_retraction_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create llm_prompts table
    op.create_table('llm_prompts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=100), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('prompt_template', sa.Text(), nullable=False),
        sa.Column('system_message', sa.Text(), nullable=True),
        sa.Column('model', sa.String(length=50), nullable=False),
        sa.Column('temperature', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deprecated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version')
    )
    op.create_index('idx_llm_prompts_task_type', 'llm_prompts', ['task_type'])
    op.create_index('idx_llm_prompts_created', 'llm_prompts', ['created_at'])
    op.create_index(op.f('ix_llm_prompts_id'), 'llm_prompts', ['id'])
    op.create_index(op.f('ix_llm_prompts_version'), 'llm_prompts', ['version'])
    op.create_index(op.f('ix_llm_prompts_task_type'), 'llm_prompts', ['task_type'])


def downgrade() -> None:
    # Drop llm_prompts table
    op.drop_index(op.f('ix_llm_prompts_task_type'), table_name='llm_prompts')
    op.drop_index(op.f('ix_llm_prompts_version'), table_name='llm_prompts')
    op.drop_index(op.f('ix_llm_prompts_id'), table_name='llm_prompts')
    op.drop_index('idx_llm_prompts_created', table_name='llm_prompts')
    op.drop_index('idx_llm_prompts_task_type', table_name='llm_prompts')
    op.drop_table('llm_prompts')
