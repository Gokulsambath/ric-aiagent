"""create_acts_table_manual

Revision ID: 1f9866453028
Revises: ac63bc585842
Create Date: 2025-12-29 21:48:38.634672

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f9866453028'
down_revision: Union[str, Sequence[str], None] = 'ac63bc585842'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create acts table with indexes and unique constraint."""
    op.create_table(
        'acts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('state', sa.Text(), nullable=True),
        sa.Column('industry', sa.Text(), nullable=True),
        sa.Column('company_type', sa.Text(), nullable=True),
        sa.Column('legislative_area', sa.Text(), nullable=True),
        sa.Column('central_acts', sa.Text(), nullable=True),
        sa.Column('state_acts', sa.Text(), nullable=True),
        sa.Column('employee_applicability', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_state_industry', 'acts', ['state', 'industry'])
    op.create_index('idx_state_legislative_area', 'acts', ['state', 'legislative_area'])
    op.create_index('idx_industry_legislative_area', 'acts', ['industry', 'legislative_area'])
    op.create_index('idx_state_industry_legislative', 'acts', ['state', 'industry', 'legislative_area'])
    op.create_index(op.f('ix_acts_state'), 'acts', ['state'], unique=False)
    op.create_index(op.f('ix_acts_industry'), 'acts', ['industry'], unique=False)
    op.create_index(op.f('ix_acts_legislative_area'), 'acts', ['legislative_area'], unique=False)
    op.create_index(op.f('ix_acts_employee_applicability'), 'acts', ['employee_applicability'], unique=False)


def downgrade() -> None:
    """Drop acts table and indexes."""
    op.drop_index(op.f('ix_acts_employee_applicability'), table_name='acts')
    op.drop_index(op.f('ix_acts_legislative_area'), table_name='acts')
    op.drop_index(op.f('ix_acts_industry'), table_name='acts')
    op.drop_index(op.f('ix_acts_state'), table_name='acts')
    op.drop_index('idx_state_industry_legislative', table_name='acts')
    op.drop_index('idx_industry_legislative_area', table_name='acts')
    op.drop_index('idx_state_legislative_area', table_name='acts')
    op.drop_index('idx_state_industry', table_name='acts')
    op.drop_table('acts')
