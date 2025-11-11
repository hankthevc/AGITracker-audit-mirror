"""Add rich content tables for educational resource transformation

Revision ID: 003_add_rich_content
Revises: 502dc116251e
Create Date: 2025-10-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '003_add_rich_content'
down_revision = '502dc116251e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to existing roadmaps table
    op.add_column('roadmaps', sa.Column('author', sa.String(255), nullable=True))
    op.add_column('roadmaps', sa.Column('published_date', sa.Date(), nullable=True))
    op.add_column('roadmaps', sa.Column('source_url', sa.Text(), nullable=True))
    op.add_column('roadmaps', sa.Column('summary', sa.Text(), nullable=True))
    
    # Add columns to existing signposts table
    op.add_column('signposts', sa.Column('short_explainer', sa.Text(), nullable=True))
    op.add_column('signposts', sa.Column('icon_emoji', sa.String(10), nullable=True))
    
    # Create roadmap_predictions table
    op.create_table(
        'roadmap_predictions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('roadmap_id', sa.Integer(), sa.ForeignKey('roadmaps.id'), nullable=False),
        sa.Column('signpost_id', sa.Integer(), sa.ForeignKey('signposts.id'), nullable=True),
        sa.Column('prediction_text', sa.Text(), nullable=False),
        sa.Column('predicted_date', sa.Date(), nullable=True),
        sa.Column('confidence_level', sa.String(20), nullable=False),
        sa.Column('source_page', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_index('idx_roadmap_predictions_roadmap', 'roadmap_predictions', ['roadmap_id'])
    op.create_index('idx_roadmap_predictions_signpost', 'roadmap_predictions', ['signpost_id'])
    
    # Add check constraint for confidence_level
    op.create_check_constraint(
        'check_confidence_level',
        'roadmap_predictions',
        "confidence_level IN ('high', 'medium', 'low')"
    )
    
    # Create signpost_content table
    op.create_table(
        'signpost_content',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('signpost_id', sa.Integer(), sa.ForeignKey('signposts.id'), nullable=False, unique=True),
        sa.Column('why_matters', sa.Text(), nullable=True),
        sa.Column('current_state', sa.Text(), nullable=True),
        sa.Column('key_papers', JSONB, nullable=True),
        sa.Column('key_announcements', JSONB, nullable=True),
        sa.Column('technical_explanation', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('idx_signpost_content_signpost', 'signpost_content', ['signpost_id'])
    
    # Create pace_analysis table
    op.create_table(
        'pace_analysis',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('signpost_id', sa.Integer(), sa.ForeignKey('signposts.id'), nullable=False),
        sa.Column('roadmap_id', sa.Integer(), sa.ForeignKey('roadmaps.id'), nullable=False),
        sa.Column('analysis_text', sa.Text(), nullable=False),
        sa.Column('last_updated', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('idx_pace_analysis_signpost', 'pace_analysis', ['signpost_id'])
    op.create_index('idx_pace_analysis_roadmap', 'pace_analysis', ['roadmap_id'])
    
    # Add unique constraint on signpost_id + roadmap_id combination
    op.create_unique_constraint(
        'uq_pace_analysis_signpost_roadmap',
        'pace_analysis',
        ['signpost_id', 'roadmap_id']
    )


def downgrade() -> None:
    # Drop new tables
    op.drop_table('pace_analysis')
    op.drop_table('signpost_content')
    op.drop_table('roadmap_predictions')
    
    # Remove columns from signposts
    op.drop_column('signposts', 'icon_emoji')
    op.drop_column('signposts', 'short_explainer')
    
    # Remove columns from roadmaps
    op.drop_column('roadmaps', 'summary')
    op.drop_column('roadmaps', 'source_url')
    op.drop_column('roadmaps', 'published_date')
    op.drop_column('roadmaps', 'author')

