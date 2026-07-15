"""link sensor logs to fermentation cycle

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sensor_logs",
        sa.Column("fermentation_cycle_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_sensor_logs_fermentation_cycle_id",
        "sensor_logs",
        "fermentation_cycles",
        ["fermentation_cycle_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_sensor_logs_fermentation_cycle_id",
        "sensor_logs",
        ["fermentation_cycle_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_sensor_logs_fermentation_cycle_id", table_name="sensor_logs")
    op.drop_constraint(
        "fk_sensor_logs_fermentation_cycle_id",
        "sensor_logs",
        type_="foreignkey",
    )
    op.drop_column("sensor_logs", "fermentation_cycle_id")
