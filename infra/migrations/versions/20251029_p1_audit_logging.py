"""Add audit logging table (P1-6)

Revision ID: 20251029_p1_audit_log
Revises: 20251029_p0_indexes
Create Date: 2025-10-29

Track all admin actions for security and compliance.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '20251029_p1_audit_log'
down_revision = '20251029_p0_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create audit_logs table."""
    
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('api_key_id', sa.Integer(), sa.ForeignKey('api_keys.id'), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('details', JSONB, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(100), nullable=True),
        sa.Column('success', sa.Boolean(), default=True, nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
    )
    
    # Indexes for common queries
    op.execute("""
        CREATE INDEX idx_audit_logs_timestamp ON audit_logs (timestamp DESC);
    """)
    
    op.execute("""
        CREATE INDEX idx_audit_logs_api_key ON audit_logs (api_key_id, timestamp DESC);
    """)
    
    op.execute("""
        CREATE INDEX idx_audit_logs_action ON audit_logs (action, timestamp DESC);
    """)
    
    op.execute("""
        CREATE INDEX idx_audit_logs_resource ON audit_logs (resource_type, resource_id);
    """)
    
    print("✅ Created audit_logs table with 4 indexes")


def downgrade() -> None:
    """Drop audit_logs table."""
    
    op.drop_table('audit_logs')
    
    print("✅ Dropped audit_logs table")

