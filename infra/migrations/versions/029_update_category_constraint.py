"""update signpost category constraint for new categories

Revision ID: 029_update_category
Revises: 028_merge_heads
Create Date: 2025-11-06

FORWARD-ONLY MIGRATION: Add 4 new signpost categories.

This migration extends the category CHECK constraint to support:
- economic: Economic indicators and market dynamics
- research: Research velocity and ecosystem metrics  
- geopolitical: International AI competition and policy
- safety_incidents: Concrete safety failures and near-misses

Original categories (capabilities, agents, inputs, security) remain unchanged.

Policy: Schema changes happen only via forward migrations, never by
editing existing migrations.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '029_update_category'
down_revision: Union[str, None] = '028_merge_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Extend category constraint to include 4 new categories.
    
    The constraint is dropped and recreated to include all 8 categories.
    This is safe because existing data only uses the 4 original categories.
    """
    
    # Drop old constraint
    op.execute("ALTER TABLE signposts DROP CONSTRAINT IF EXISTS check_signpost_category")
    
    # Add new constraint with all 8 categories
    op.execute("""
        ALTER TABLE signposts ADD CONSTRAINT check_signpost_category
        CHECK (category IN ('capabilities','agents','inputs','security',
                           'economic','research','geopolitical','safety_incidents'))
    """)
    
    # Add unique index on signpost code to prevent duplicates
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_signposts_code ON signposts(code)")
    
    print("✓ Updated category constraint with 4 new categories")
    print("✓ Added unique constraint on signpost code")


def downgrade() -> None:
    """
    Restore original 4-category constraint.
    
    WARNING: This will fail if any signposts exist with the new categories.
    """
    
    # Drop unique index
    op.execute("DROP INDEX IF EXISTS uq_signposts_code")
    
    # Drop extended constraint
    op.execute("ALTER TABLE signposts DROP CONSTRAINT IF EXISTS check_signpost_category")
    
    # Restore original 4-category constraint
    op.execute("""
        ALTER TABLE signposts ADD CONSTRAINT check_signpost_category
        CHECK (category IN ('capabilities', 'agents', 'inputs', 'security'))
    """)
    
    print("✓ Restored original 4-category constraint")
    print("⚠️  Signposts with new categories will fail validation")

