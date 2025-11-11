"""add roadmap_predictions table

Revision ID: 004_roadmap_predictions
Revises: 003_add_rich_content
Create Date: 2025-10-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_roadmap_predictions'
down_revision = '003_add_rich_content'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add signpost_code column to roadmap_predictions for AI-2027 scenario alignment."""
    # Table already exists from 003_add_rich_content, just add signpost_code column
    op.add_column('roadmap_predictions', sa.Column('signpost_code', sa.String(100), nullable=True))
    op.create_index('idx_roadmap_predictions_signpost_code', 'roadmap_predictions', ['signpost_code'])


def downgrade() -> None:
    """Remove signpost_code column from roadmap_predictions."""
    op.drop_index('idx_roadmap_predictions_signpost_code', table_name='roadmap_predictions')
    op.drop_column('roadmap_predictions', 'signpost_code')

