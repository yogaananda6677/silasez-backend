"""add video message type

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
"""

from alembic import op

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'VIDEO'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely without rebuilding
    # the type. Leaving the value is backward-compatible.
    pass
