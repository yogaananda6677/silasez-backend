"""add_photo_url_to_users

Revision ID: 75129ad9365e
Revises: 19de85940021
Create Date: 2026-07-04 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75129ad9365e'
down_revision: Union[str, Sequence[str], None] = '19de85940021'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column('photo_url', sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'photo_url')
