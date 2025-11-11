"""add openai_prep_confidence field

Revision ID: 030_openai_prep_conf
Revises: 029_update_category
Create Date: 2025-11-06

FORWARD-ONLY MIGRATION: Add confidence field for OpenAI Preparedness forecasts.

This field was originally added via ad-hoc script, which violates the
"schema changes only via forward migrations" policy.

This migration properly adds the column with a CHECK constraint to
ensure values are between 0 and 1 (percentage as decimal).

Policy: All schema changes must go through Alembic migrations, never
via ad-hoc scripts or editing existing migrations.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '030_openai_prep_conf'
down_revision: Union[str, None] = '029_update_category'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add openai_prep_confidence column.
    
    Stores confidence level (0.0 to 1.0) for OpenAI Preparedness Framework
    timeline predictions.
    """
    
    op.execute("""
        ALTER TABLE signposts 
        ADD COLUMN IF NOT EXISTS openai_prep_confidence NUMERIC 
        CHECK (openai_prep_confidence >= 0 AND openai_prep_confidence <= 1)
    """)
    
    print("✓ Added openai_prep_confidence column")


def downgrade() -> None:
    """Remove openai_prep_confidence column."""
    
    op.execute("ALTER TABLE signposts DROP COLUMN IF EXISTS openai_prep_confidence")
    
    print("✓ Removed openai_prep_confidence column")

