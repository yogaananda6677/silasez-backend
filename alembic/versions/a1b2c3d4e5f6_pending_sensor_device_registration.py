"""pending sensor device registration

Revision ID: a1b2c3d4e5f6
Revises: 077791dd362c
Create Date: 2026-07-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '077791dd362c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Tambah value 'pending' ke enum sensor_status (device baru = pending sebelum di-approve admin)
    op.execute("ALTER TYPE sensor_status ADD VALUE IF NOT EXISTS 'pending'")

    # silo_id boleh kosong dulu, diisi saat admin approve & assign device ke silo
    op.alter_column(
        'sensors',
        'silo_id',
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Catatan: Postgres tidak mendukung penghapusan value enum secara langsung.
    # Untuk downgrade penuh, enum sensor_status perlu dibuat ulang manual jika diperlukan.
    op.alter_column(
        'sensors',
        'silo_id',
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=False,
    )
