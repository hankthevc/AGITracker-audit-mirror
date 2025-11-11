"""add performance indexes

Revision ID: perf_indexes_001
Revises: (update_with_previous_revision)
Create Date: 2025-10-28

Adds strategic indexes for common query patterns:
- Event filters (needs_review, provisional, retracted)
- EventSignpostLink queries (event_id, signpost_id, confidence)
- EventAnalysis lookups
- ExpertPrediction queries
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'perf_indexes_001'
down_revision = '016_news_pipeline'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes."""
    
    # Events table - common filters
    op.create_index(
        'idx_events_needs_review', 
        'events', 
        ['needs_review', 'published_at'],
        postgresql_where=sa.text('needs_review = true')
    )
    op.create_index(
        'idx_events_provisional',
        'events',
        ['provisional', 'evidence_tier']
    )
    op.create_index(
        'idx_events_source_type',
        'events',
        ['source_type', 'evidence_tier', 'published_at']
    )
    
    # EventSignpostLink table - join and filter performance
    op.create_index(
        'idx_event_signpost_links_event_id',
        'event_signpost_links',
        ['event_id']
    )
    op.create_index(
        'idx_event_signpost_links_signpost_id',
        'event_signpost_links',
        ['signpost_id', 'observed_at']
    )
    op.create_index(
        'idx_event_signpost_links_confidence',
        'event_signpost_links',
        ['confidence'],
        postgresql_where=sa.text('needs_review = true')
    )
    
    # EventAnalysis table - lookups
    op.create_index(
        'idx_event_analysis_event_id',
        'events_analysis',
        ['event_id']
    )
    op.create_index(
        'idx_event_analysis_significance',
        'events_analysis',
        ['significance_score', 'generated_at']
    )
    
    # ExpertPrediction table - comparisons
    op.create_index(
        'idx_expert_predictions_signpost',
        'expert_predictions',
        ['signpost_id', 'predicted_date']
    )
    op.create_index(
        'idx_expert_predictions_source',
        'expert_predictions',
        ['source', 'predicted_date']
    )
    
    # RoadmapPrediction table - forecasts
    op.create_index(
        'idx_roadmap_predictions_signpost',
        'roadmap_predictions',
        ['signpost_id', 'predicted_date']
    )
    
    print("✅ Added performance indexes")


def downgrade():
    """Remove performance indexes."""
    
    # Events indexes
    op.drop_index('idx_events_needs_review', table_name='events')
    op.drop_index('idx_events_provisional', table_name='events')
    op.drop_index('idx_events_source_type', table_name='events')
    
    # EventSignpostLink indexes
    op.drop_index('idx_event_signpost_links_event_id', table_name='event_signpost_links')
    op.drop_index('idx_event_signpost_links_signpost_id', table_name='event_signpost_links')
    op.drop_index('idx_event_signpost_links_confidence', table_name='event_signpost_links')
    
    # EventAnalysis indexes
    op.drop_index('idx_event_analysis_event_id', table_name='events_analysis')
    op.drop_index('idx_event_analysis_significance', table_name='events_analysis')
    
    # ExpertPrediction indexes
    op.drop_index('idx_expert_predictions_signpost', table_name='expert_predictions')
    op.drop_index('idx_expert_predictions_source', table_name='expert_predictions')
    
    # RoadmapPrediction indexes
    op.drop_index('idx_roadmap_predictions_signpost', table_name='roadmap_predictions')
    
    print("✅ Removed performance indexes")

