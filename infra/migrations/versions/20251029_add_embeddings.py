"""add embeddings to events and signposts

Revision ID: 20251029_add_embeddings
Revises: 020_performance_optimizations
Create Date: 2025-10-29

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '20251029_add_embeddings'
down_revision = '020_performance_optimizations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add embedding columns and HNSW indexes.
    
    TEMPORARILY DISABLED: Requires pgvector extension which is not installed
    in production database. Enable when ready to use Phase 4 RAG features.
    
    To re-enable:
    1. Run: CREATE EXTENSION IF NOT EXISTS vector; (in production database)
    2. Uncomment the implementation below
    3. Redeploy
    """
    # MIGRATION TEMPORARILY DISABLED - PASS THROUGH
    # This allows migration chain to complete without pgvector dependency
    pass


def downgrade() -> None:
    """Remove embedding columns and indexes (DISABLED)."""
    # Migration disabled - nothing to downgrade
    pass

