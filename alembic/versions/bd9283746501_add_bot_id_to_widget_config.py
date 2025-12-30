"""add_bot_id_to_widget_config

Revision ID: bd9283746501
Revises: ac63bc585842
Create Date: 2025-12-30 12:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = 'bd9283746501'
down_revision: Union[str, Sequence[str], None] = 'ac63bc585842'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add bot_id column to widget_config
    op.add_column('widget_config', sa.Column('bot_id', sa.String(length=50), nullable=True))

    # 2. Update Data
    # We use valid SQL that should work on SQLite/Postgres
    conn = op.get_bind()
    
    # Update ric-tenant
    conn.execute(text("UPDATE widget_config SET bot_id = 'ric' WHERE tenant_id = 'ric-tenant'"))
    
    # Update cms-tenant
    conn.execute(text("UPDATE widget_config SET bot_id = 'ric-cms' WHERE tenant_id = 'cms-tenant'"))


def downgrade() -> None:
    # Drop bot_id column
    op.drop_column('widget_config', 'bot_id')
