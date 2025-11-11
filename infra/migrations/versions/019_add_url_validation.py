"""add url validation fields for Sprint 10

Revision ID: 019_url_validation
Revises: 018_performance_indexes
Create Date: 2025-10-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP


# revision identifiers, used by Alembic.
revision: str = '019_url_validation'
down_revision: Union[str, None] = '018_performance_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add URL validation fields to events table for Sprint 10.
    
    These fields track the accessibility and health of source URLs:
    - url_validated_at: When URL was last checked
    - url_status_code: HTTP status code (200, 404, etc.)
    - url_is_valid: Boolean flag for quick filtering
    - url_error: Error message if validation failed
    """
    
    # Add URL validation timestamp
    with op.get_context().autocommit_block():
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'events' AND column_name = 'url_validated_at'
                ) THEN
                    ALTER TABLE events 
                    ADD COLUMN url_validated_at TIMESTAMPTZ NULL;
                END IF;
            END $$;
        """)
    
    # Add HTTP status code
    with op.get_context().autocommit_block():
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'events' AND column_name = 'url_status_code'
                ) THEN
                    ALTER TABLE events 
                    ADD COLUMN url_status_code INTEGER NULL;
                END IF;
            END $$;
        """)
    
    # Add validation flag (defaults to TRUE for existing events)
    with op.get_context().autocommit_block():
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'events' AND column_name = 'url_is_valid'
                ) THEN
                    ALTER TABLE events 
                    ADD COLUMN url_is_valid BOOLEAN DEFAULT TRUE NOT NULL;
                END IF;
            END $$;
        """)
    
    # Add error message field
    with op.get_context().autocommit_block():
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'events' AND column_name = 'url_error'
                ) THEN
                    ALTER TABLE events 
                    ADD COLUMN url_error TEXT NULL;
                END IF;
            END $$;
        """)
    
    # Create index on url_is_valid for fast filtering of invalid URLs
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_url_invalid 
            ON events(url_is_valid) 
            WHERE url_is_valid = FALSE;
        """)
    
    # Create index on url_validated_at for finding stale validations
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_url_validated_at 
            ON events(url_validated_at) 
            WHERE url_validated_at IS NOT NULL;
        """)


def downgrade() -> None:
    """
    Remove URL validation fields.
    """
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_events_url_validated_at")
    op.execute("DROP INDEX IF EXISTS idx_events_url_invalid")
    
    # Drop columns
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'events' AND column_name = 'url_error'
            ) THEN
                ALTER TABLE events DROP COLUMN url_error;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'events' AND column_name = 'url_is_valid'
            ) THEN
                ALTER TABLE events DROP COLUMN url_is_valid;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'events' AND column_name = 'url_status_code'
            ) THEN
                ALTER TABLE events DROP COLUMN url_status_code;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'events' AND column_name = 'url_validated_at'
            ) THEN
                ALTER TABLE events DROP COLUMN url_validated_at;
            END IF;
        END $$;
    """)
