"""Phase 2/3 stub tables: expert predictions and accuracy tracking

Revision ID: 20251020115051
Revises: 20251020115050
Create Date: 2025-10-20 11:50:51.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251020115051'
down_revision: Union[str, None] = '20251020115050'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create expert_predictions table (Phase 3)
    # Stores predictions from experts, roadmaps, and forecasting platforms
    op.create_table(
        'expert_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(255), nullable=True),
        sa.Column('signpost_id', sa.Integer(), nullable=True),
        sa.Column('predicted_date', sa.Date(), nullable=True),
        sa.Column('predicted_value', sa.Numeric(), nullable=True),
        sa.Column('confidence_lower', sa.Numeric(), nullable=True),
        sa.Column('confidence_upper', sa.Numeric(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('added_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['signpost_id'], ['signposts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create prediction_accuracy table (Phase 3)
    # Tracks calibration and accuracy of expert predictions
    op.create_table(
        'prediction_accuracy',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prediction_id', sa.Integer(), nullable=True),
        sa.Column('evaluated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('actual_value', sa.Numeric(), nullable=True),
        sa.Column('error_magnitude', sa.Numeric(), nullable=True),
        sa.Column('directional_correct', sa.Boolean(), nullable=True),
        sa.Column('calibration_score', sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(['prediction_id'], ['expert_predictions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for common queries
    op.create_index('idx_expert_predictions_signpost', 'expert_predictions', ['signpost_id'])
    op.create_index('idx_expert_predictions_date', 'expert_predictions', ['predicted_date'])
    op.create_index('idx_prediction_accuracy_prediction', 'prediction_accuracy', ['prediction_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_prediction_accuracy_prediction', table_name='prediction_accuracy')
    op.drop_index('idx_expert_predictions_date', table_name='expert_predictions')
    op.drop_index('idx_expert_predictions_signpost', table_name='expert_predictions')
    
    # Drop tables
    op.drop_table('prediction_accuracy')
    op.drop_table('expert_predictions')

