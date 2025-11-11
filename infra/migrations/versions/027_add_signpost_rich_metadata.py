"""add rich metadata fields to signposts

Revision ID: 027_rich_metadata
Revises: 026_concurrent_rebuild  
Create Date: 2025-11-07

FEATURE: Add comprehensive metadata fields to support 89-signpost expansion.

Fields added:
- why_matters (TEXT) - Strategic/economic importance
- measurement_methodology (TEXT) - How to track this signpost
- measurement_source (TEXT) - URL/API for data
- measurement_frequency (TEXT) - How often updated
- current_sota_value (NUMERIC) - Latest known performance
- current_sota_model (TEXT) - Which model/system
- current_sota_date (DATE) - When measured
- aschenbrenner_timeline (DATE) - Aschenbrenner's prediction
- aschenbrenner_confidence (NUMERIC) - Confidence level
- aschenbrenner_quote (TEXT) - Actual quote from source
- ai2027_timeline (DATE) - AI 2027 prediction
- cotra_timeline (DATE) - Cotra bio anchors
- epoch_timeline (DATE) - Epoch AI prediction
- related_signpost_codes (TEXT) - Comma-separated prerequisite codes
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '027_rich_metadata'
down_revision: Union[str, None] = '026_concurrent_rebuild'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add rich metadata fields to signposts table."""
    
    # Strategic context
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS why_matters TEXT")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS strategic_importance TEXT")
    
    # Measurement details
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS measurement_methodology TEXT")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS measurement_source TEXT")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS measurement_frequency TEXT")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS verification_tier TEXT")
    
    # Current state of the art
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS current_sota_value NUMERIC")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS current_sota_model TEXT")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS current_sota_date DATE")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS current_sota_source TEXT")
    
    # Expert forecasts (Aschenbrenner)
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS aschenbrenner_timeline DATE")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS aschenbrenner_confidence NUMERIC CHECK (aschenbrenner_confidence >= 0 AND aschenbrenner_confidence <= 1)")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS aschenbrenner_quote TEXT")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS aschenbrenner_rationale TEXT")
    
    # Expert forecasts (AI 2027)
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS ai2027_timeline DATE")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS ai2027_confidence NUMERIC CHECK (ai2027_confidence >= 0 AND ai2027_confidence <= 1)")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS ai2027_rationale TEXT")
    
    # Expert forecasts (Cotra)
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS cotra_timeline DATE")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS cotra_confidence NUMERIC CHECK (cotra_confidence >= 0 AND cotra_confidence <= 1)")
    
    # Expert forecasts (Epoch AI)
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS epoch_timeline DATE")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS epoch_confidence NUMERIC CHECK (epoch_confidence >= 0 AND epoch_confidence <= 1)")
    
    # Expert forecasts (OpenAI Preparedness)
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS openai_prep_timeline DATE")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS openai_prep_risk_level TEXT")
    
    # Citations and sources
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS primary_paper_title TEXT")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS primary_paper_url TEXT")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS primary_paper_authors TEXT")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS primary_paper_year INTEGER")
    
    # Relationships
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS prerequisite_codes TEXT")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS related_signpost_codes TEXT")
    
    # Display metadata
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS display_order INTEGER")
    op.execute("ALTER TABLE signposts ADD COLUMN IF NOT EXISTS is_negative_indicator BOOLEAN DEFAULT FALSE")
    
    print(f"✓ Added 30+ rich metadata fields to signposts table")


def downgrade() -> None:
    """Remove rich metadata fields."""
    
    # Note: In production, you might want to keep these columns
    # For development, we can drop them
    
    columns_to_drop = [
        'why_matters', 'strategic_importance',
        'measurement_methodology', 'measurement_source', 'measurement_frequency', 'verification_tier',
        'current_sota_value', 'current_sota_model', 'current_sota_date', 'current_sota_source',
        'aschenbrenner_timeline', 'aschenbrenner_confidence', 'aschenbrenner_quote', 'aschenbrenner_rationale',
        'ai2027_timeline', 'ai2027_confidence', 'ai2027_rationale',
        'cotra_timeline', 'cotra_confidence',
        'epoch_timeline', 'epoch_confidence',
        'openai_prep_timeline', 'openai_prep_risk_level',
        'primary_paper_title', 'primary_paper_url', 'primary_paper_authors', 'primary_paper_year',
        'prerequisite_codes', 'related_signpost_codes',
        'display_order', 'is_negative_indicator'
    ]
    
    for col in columns_to_drop:
        op.execute(f"ALTER TABLE signposts DROP COLUMN IF EXISTS {col}")
    
    print(f"✓ Removed rich metadata fields")

