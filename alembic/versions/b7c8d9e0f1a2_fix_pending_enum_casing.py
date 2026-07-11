"""fix pending enum value casing

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-07-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Migration sebelumnya (a1b2c3d4e5f6) salah nambahin 'pending' huruf kecil,
    # padahal enum sensor_status yang asli pakai huruf besar (ACTIVE, OFFLINE, ERROR).
    # Tambahkan value yang benar: 'PENDING'
    op.execute("ALTER TYPE sensor_status ADD VALUE IF NOT EXISTS 'PENDING'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres tidak mendukung penghapusan value enum secara langsung.
    pass