"""add audit logs for admin actions

Revision ID: 025_audit_logs
Revises: 024_composite_indexes
Create Date: 2025-11-06

SECURITY: Audit logging for compliance and forensics.

GPT-5 Pro audit recommendation: Track all administrative actions
for security compliance, incident response, and accountability.

Tracks: Who did what, when, from where, with which API key.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '025_audit_logs'
down_revision: Union[str, None] = '024_composite_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit_logs table for admin action tracking."""
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            action TEXT NOT NULL,                    -- "approve", "reject", "retract", "trigger_ingestion"
            resource_type TEXT NOT NULL,             -- "event", "mapping", "system"
            resource_id INTEGER,                     -- Event ID, mapping ID, etc.
            api_key_hash TEXT,                       -- First 8 chars of API key (for identification)
            ip_address INET,                         -- Client IP
            user_agent TEXT,                         -- Client user agent
            request_path TEXT,                       -- Full request path
            success BOOLEAN DEFAULT TRUE,            -- Did action succeed?
            error_message TEXT,                      -- Error if failed
            metadata JSONB                           -- Additional context
        );
    """)
    
    # Index for querying by timestamp (recent actions)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp
        ON audit_logs(timestamp DESC);
    """)
    
    # Index for querying by action type
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_logs_action
        ON audit_logs(action, timestamp DESC);
    """)
    
    # Index for querying by resource
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_logs_resource
        ON audit_logs(resource_type, resource_id);
    """)


def downgrade() -> None:
    """Remove audit_logs table."""
    
    op.execute("DROP TABLE IF EXISTS audit_logs CASCADE")

