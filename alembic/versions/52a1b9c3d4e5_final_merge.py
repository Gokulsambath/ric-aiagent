"""final_merge_to_single_head

Revision ID: 52a1b9c3d4e5
Revises: bd9283746501, ef6e3d91fb64
Create Date: 2025-12-30 17:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52a1b9c3d4e5'
down_revision: Union[str, Sequence[str], None] = ('bd9283746501', 'ef6e3d91fb64')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
