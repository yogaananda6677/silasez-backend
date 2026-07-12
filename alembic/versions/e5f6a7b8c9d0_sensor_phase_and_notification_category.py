"""sensor phase and notification category

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
"""

from alembic import op
import sqlalchemy as sa


revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE fermentation_cycles
        SET planned_duration_days = 21,
            end_date = start_date + INTERVAL '20 days'
        WHERE status = 'RUNNING'
        """
    )
    op.add_column(
        "sensor_logs",
        sa.Column("fermentation_day", sa.Integer(), nullable=True),
    )
    op.add_column(
        "sensor_logs",
        sa.Column(
            "phase",
            sa.String(length=30),
            nullable=False,
            server_default="monitoring",
        ),
    )
    op.create_table(
        "device_tokens",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token", sa.String(length=512), nullable=False),
        sa.Column("platform", sa.String(length=30), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("ix_device_tokens_user_id", "device_tokens", ["user_id"])
    op.create_index("ix_device_tokens_token", "device_tokens", ["token"], unique=True)
    op.add_column(
        "sensor_logs",
        sa.Column("classification", sa.String(length=80), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "category",
            sa.String(length=30),
            nullable=False,
            server_default="system",
        ),
    )


def downgrade() -> None:
    op.drop_index("ix_device_tokens_token", table_name="device_tokens")
    op.drop_index("ix_device_tokens_user_id", table_name="device_tokens")
    op.drop_table("device_tokens")
    op.drop_column("notifications", "category")
    op.drop_column("sensor_logs", "classification")
    op.drop_column("sensor_logs", "phase")
    op.drop_column("sensor_logs", "fermentation_day")
