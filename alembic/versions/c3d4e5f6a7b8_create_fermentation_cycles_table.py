"""create fermentation cycles table

Revision ID: c3d4e5f6a7b8
Revises: b7c8d9e0f1a2
Create Date: 2026-07-10 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'fermentation_cycles',
        sa.Column('silo_id', sa.UUID(), nullable=False),
        sa.Column('started_by', sa.UUID(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('planned_duration_days', sa.Integer(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('actual_end_date', sa.Date(), nullable=True),
        # NB: value enum di Postgres pakai NAMA member Python
        # (RUNNING/COMPLETED/CANCELLED), bukan .value-nya — samain dengan
        # pola enum lain di codebase ini (lihat migration
        # b7c8d9e0f1a2_fix_pending_enum_casing.py, dulu pernah salah pakai
        # huruf kecil di sini).
        sa.Column(
            'status',
            sa.Enum('RUNNING', 'COMPLETED', 'CANCELLED', name='fermentation_status'),
            nullable=False,
        ),
        sa.Column('catatan', sa.Text(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['silo_id'], ['silos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['started_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(
        op.f('ix_fermentation_cycles_silo_id'),
        'fermentation_cycles',
        ['silo_id'],
        unique=False,
    )

    # 1 silo cuma boleh punya 1 siklus RUNNING dalam satu waktu. Ini
    # jaring pengaman terakhir di level database, komplemen dari
    # pengecekan di FermentationService.start() (yang ngasih pesan error
    # yang enak dibaca) — partial unique index tetap benar walau ada 2
    # request bareng-bareng (race condition) yang lolos dari pengecekan
    # aplikasi.
    op.create_index(
        'uq_one_running_cycle_per_silo',
        'fermentation_cycles',
        ['silo_id'],
        unique=True,
        postgresql_where=sa.text("status = 'RUNNING'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_one_running_cycle_per_silo', table_name='fermentation_cycles')
    op.drop_index(op.f('ix_fermentation_cycles_silo_id'), table_name='fermentation_cycles')
    op.drop_table('fermentation_cycles')
    op.execute('DROP TYPE IF EXISTS fermentation_status')
