"""Add monthly_updates table

Revision ID: 003_add_monthly_updates_table
Revises: 002_add_leads_table
Create Date: 2026-01-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_add_monthly_updates_table'
down_revision: Union[str, Sequence[str], None] = '002_add_leads_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create monthly_updates table."""
    # Check if table already exists, if not create it
    from sqlalchemy import inspect
    
    connection = op.get_bind()
    inspector = inspect(connection)
    tables = inspector.get_table_names()
    
    if 'monthly_updates' not in tables:
        # Create the monthly_updates table
        op.create_table('monthly_updates',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.Text(), nullable=False),
            sa.Column('category', sa.Text(), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('change_type', sa.Text(), nullable=False),
            sa.Column('state', sa.Text(), nullable=False),
            sa.Column('effective_date', sa.Date(), nullable=False),
            sa.Column('update_date', sa.Date(), nullable=False),
            sa.Column('source_link', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create indexes (check if they exist first)
    indexes = inspector.get_indexes('monthly_updates') if 'monthly_updates' in tables else []
    existing_index_names = {idx['name'] for idx in indexes}
    
    if 'ix_monthly_updates_title' not in existing_index_names:
        op.create_index('ix_monthly_updates_title', 'monthly_updates', ['title'])
    if 'ix_monthly_updates_category' not in existing_index_names:
        op.create_index('ix_monthly_updates_category', 'monthly_updates', ['category'])
    if 'ix_monthly_updates_change_type' not in existing_index_names:
        op.create_index('ix_monthly_updates_change_type', 'monthly_updates', ['change_type'])
    if 'ix_monthly_updates_state' not in existing_index_names:
        op.create_index('ix_monthly_updates_state', 'monthly_updates', ['state'])
    if 'ix_monthly_updates_effective_date' not in existing_index_names:
        op.create_index('ix_monthly_updates_effective_date', 'monthly_updates', ['effective_date'])
    if 'ix_monthly_updates_update_date' not in existing_index_names:
        op.create_index('ix_monthly_updates_update_date', 'monthly_updates', ['update_date'])
    if 'idx_effective_date' not in existing_index_names:
        op.create_index('idx_effective_date', 'monthly_updates', ['effective_date'])
    if 'idx_update_date' not in existing_index_names:
        op.create_index('idx_update_date', 'monthly_updates', ['update_date'])
    if 'idx_category_effective_date' not in existing_index_names:
        op.create_index('idx_category_effective_date', 'monthly_updates', ['category', 'effective_date'])
    if 'idx_category_state' not in existing_index_names:
        op.create_index('idx_category_state', 'monthly_updates', ['category', 'state'])
    if 'idx_category_change_type' not in existing_index_names:
        op.create_index('idx_category_change_type', 'monthly_updates', ['category', 'change_type'])
    if 'idx_state_change_type' not in existing_index_names:
        op.create_index('idx_state_change_type', 'monthly_updates', ['state', 'change_type'])


def downgrade() -> None:
    """Drop monthly_updates table."""
    op.drop_table('monthly_updates')