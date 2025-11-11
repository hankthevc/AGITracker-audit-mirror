"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2025-10-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create roadmaps table
    op.create_table('roadmaps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('preset_weights', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_roadmaps_id'), 'roadmaps', ['id'], unique=False)
    op.create_index(op.f('ix_roadmaps_slug'), 'roadmaps', ['slug'], unique=False)
    
    # Create signposts table
    op.create_table('signposts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('roadmap_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=20), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('direction', sa.String(length=5), nullable=False),
        sa.Column('baseline_value', sa.Numeric(), nullable=True),
        sa.Column('target_value', sa.Numeric(), nullable=True),
        sa.Column('methodology_url', sa.Text(), nullable=True),
        sa.Column('first_class', sa.Boolean(), nullable=True),
        sa.Column('embedding', sa.Text(), nullable=True),  # Will be cast to VECTOR after creation
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint("category IN ('capabilities', 'agents', 'inputs', 'security')", name='check_signpost_category'),
        sa.CheckConstraint("direction IN ('>=', '<=')", name='check_signpost_direction'),
        sa.ForeignKeyConstraint(['roadmap_id'], ['roadmaps.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_signposts_code'), 'signposts', ['code'], unique=False)
    op.create_index(op.f('ix_signposts_id'), 'signposts', ['id'], unique=False)
    op.create_index('idx_signposts_category', 'signposts', ['category'], unique=False)
    op.create_index('idx_signposts_first_class', 'signposts', ['first_class'], unique=False)
    
    # Convert embedding column to vector type
    op.execute('ALTER TABLE signposts ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector')
    
    # Create benchmarks table
    op.create_table('benchmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('family', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint("family IN ('SWE_BENCH_VERIFIED', 'OSWORLD', 'WEBARENA', 'GPQA_DIAMOND', 'OTHER')", name='check_benchmark_family'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_benchmarks_code'), 'benchmarks', ['code'], unique=False)
    op.create_index(op.f('ix_benchmarks_id'), 'benchmarks', ['id'], unique=False)
    
    # Create sources table
    op.create_table('sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('credibility', sa.String(length=1), nullable=False),
        sa.Column('first_seen_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint("credibility IN ('A', 'B', 'C', 'D')", name='check_credibility'),
        sa.CheckConstraint("source_type IN ('paper', 'leaderboard', 'model_card', 'press', 'blog', 'social')", name='check_source_type'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )
    op.create_index(op.f('ix_sources_id'), 'sources', ['id'], unique=False)
    op.create_index('idx_sources_credibility', 'sources', ['credibility'], unique=False)
    
    # Create claims table
    op.create_table('claims',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('metric_name', sa.String(length=100), nullable=True),
        sa.Column('metric_value', sa.Numeric(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('observed_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('url_hash', sa.String(length=64), nullable=True),
        sa.Column('extraction_confidence', sa.Numeric(), nullable=True),
        sa.Column('raw_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('retracted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url_hash')
    )
    op.create_index(op.f('ix_claims_id'), 'claims', ['id'], unique=False)
    op.create_index('idx_claims_observed_at', 'claims', ['observed_at'], unique=False)
    op.create_index('idx_claims_retracted', 'claims', ['retracted'], unique=False)
    
    # Create claim_benchmarks table
    op.create_table('claim_benchmarks',
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('benchmark_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['benchmark_id'], ['benchmarks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('claim_id', 'benchmark_id')
    )
    
    # Create claim_signposts table
    op.create_table('claim_signposts',
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('signpost_id', sa.Integer(), nullable=False),
        sa.Column('fit_score', sa.Numeric(), nullable=True),
        sa.Column('impact_estimate', sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['signpost_id'], ['signposts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('claim_id', 'signpost_id')
    )
    
    # Create changelog table
    op.create_table('changelog',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('occurred_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('claim_id', sa.Integer(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint("type IN ('add', 'update', 'retract')", name='check_changelog_type'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_changelog_id'), 'changelog', ['id'], unique=False)
    
    # Create index_snapshots table
    op.create_table('index_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('as_of_date', sa.Date(), nullable=False),
        sa.Column('capabilities', sa.Numeric(), nullable=True),
        sa.Column('agents', sa.Numeric(), nullable=True),
        sa.Column('inputs', sa.Numeric(), nullable=True),
        sa.Column('security', sa.Numeric(), nullable=True),
        sa.Column('overall', sa.Numeric(), nullable=True),
        sa.Column('safety_margin', sa.Numeric(), nullable=True),
        sa.Column('preset', sa.String(length=50), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('as_of_date')
    )
    op.create_index(op.f('ix_index_snapshots_id'), 'index_snapshots', ['id'], unique=False)
    
    # Create weekly_digest table
    op.create_table('weekly_digest',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('week_start')
    )
    op.create_index(op.f('ix_weekly_digest_id'), 'weekly_digest', ['id'], unique=False)
    
    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('hashed_key', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint("role IN ('admin', 'readonly')", name='check_api_key_role'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hashed_key')
    )
    op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_api_keys_id'), table_name='api_keys')
    op.drop_table('api_keys')
    op.drop_index(op.f('ix_weekly_digest_id'), table_name='weekly_digest')
    op.drop_table('weekly_digest')
    op.drop_index(op.f('ix_index_snapshots_id'), table_name='index_snapshots')
    op.drop_table('index_snapshots')
    op.drop_index(op.f('ix_changelog_id'), table_name='changelog')
    op.drop_table('changelog')
    op.drop_table('claim_signposts')
    op.drop_table('claim_benchmarks')
    op.drop_index('idx_claims_retracted', table_name='claims')
    op.drop_index('idx_claims_observed_at', table_name='claims')
    op.drop_index(op.f('ix_claims_id'), table_name='claims')
    op.drop_table('claims')
    op.drop_index('idx_sources_credibility', table_name='sources')
    op.drop_index(op.f('ix_sources_id'), table_name='sources')
    op.drop_table('sources')
    op.drop_index(op.f('ix_benchmarks_id'), table_name='benchmarks')
    op.drop_index(op.f('ix_benchmarks_code'), table_name='benchmarks')
    op.drop_table('benchmarks')
    op.drop_index('idx_signposts_first_class', table_name='signposts')
    op.drop_index('idx_signposts_category', table_name='signposts')
    op.drop_index(op.f('ix_signposts_id'), table_name='signposts')
    op.drop_index(op.f('ix_signposts_code'), table_name='signposts')
    op.drop_table('signposts')
    op.drop_index(op.f('ix_roadmaps_slug'), table_name='roadmaps')
    op.drop_index(op.f('ix_roadmaps_id'), table_name='roadmaps')
    op.drop_table('roadmaps')
    
    op.execute('DROP EXTENSION IF EXISTS vector')

