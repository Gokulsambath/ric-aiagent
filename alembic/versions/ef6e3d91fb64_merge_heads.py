"""merge_heads

Revision ID: ef6e3d91fb64
Revises: e644a9a4dc16, 1f9866453028
Create Date: 2025-12-29 21:51:48.805783

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef6e3d91fb64'
down_revision: Union[str, Sequence[str], None] = ('e644a9a4dc16', '1f9866453028')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
