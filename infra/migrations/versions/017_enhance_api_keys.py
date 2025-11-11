"""enhance api keys table for sprint 8

Revision ID: 017_enhance_api_keys
Revises: 016_news_pipeline
Create Date: 2025-10-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '017_enhance_api_keys'
down_revision: Union[str, None] = '016_news_pipeline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enhance API keys table for Sprint 8 authentication and rate limiting.
    
    Changes:
    - Drop old api_keys table if it exists
    - Create new api_keys table with enhanced schema
    - Add tier-based authentication (public, authenticated, admin)
    - Add usage tracking fields
    - Add custom rate limits
    """
    
    # Drop old table if exists (safe to do - no production data yet)
    op.execute("DROP TABLE IF EXISTS api_keys CASCADE")
    
    # Create new api_keys table with enhanced schema
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('tier', sa.Enum('public', 'authenticated', 'admin', name='api_key_tier'), nullable=False, server_default='authenticated'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_used_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rate_limit', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("tier IN ('public', 'authenticated', 'admin')", name='check_api_key_tier')
    )
    
    # Create indexes
    op.create_index('idx_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)
    op.create_index('idx_api_keys_created_at', 'api_keys', ['created_at'])
    op.create_index('idx_api_keys_active_tier', 'api_keys', ['is_active', 'tier'])


def downgrade() -> None:
    """
    Revert API keys table changes.
    """
    op.drop_index('idx_api_keys_active_tier', table_name='api_keys')
    op.drop_index('idx_api_keys_created_at', table_name='api_keys')
    op.drop_index('idx_api_keys_key_hash', table_name='api_keys')
    op.drop_table('api_keys')
    op.execute("DROP TYPE IF EXISTS api_key_tier")
