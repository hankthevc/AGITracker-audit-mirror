"""add approved_at to event_signpost_links

Revision ID: 009a_add_link_approved_at
Revises: 009_add_review_fields
Create Date: 2025-10-20

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "009a_add_link_approved_at"
down_revision: Union[str, None] = "009_add_review_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "event_signpost_links",
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "event_signpost_links",
        sa.Column("approved_by", sa.String(100), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("event_signpost_links", "approved_by")
    op.drop_column("event_signpost_links", "approved_at")

