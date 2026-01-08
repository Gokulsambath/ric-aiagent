"""Add leads table

Revision ID: 002_add_leads_table
Revises: 001_initial_schema
Create Date: 2026-01-09 01:11:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002_add_leads_table'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create leads table."""
    op.create_table(
        'leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('contact_person_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('mobile_number', sa.String(length=50), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('thread_id', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index(op.f('ix_leads_company_name'), 'leads', ['company_name'], unique=False)
    op.create_index(op.f('ix_leads_contact_person_name'), 'leads', ['contact_person_name'], unique=False)
    op.create_index(op.f('ix_leads_email'), 'leads', ['email'], unique=False)
    op.create_index(op.f('ix_leads_session_id'), 'leads', ['session_id'], unique=False)
    op.create_index(op.f('ix_leads_thread_id'), 'leads', ['thread_id'], unique=False)


def downgrade() -> None:
    """Drop leads table."""
    op.drop_index(op.f('ix_leads_thread_id'), table_name='leads')
    op.drop_index(op.f('ix_leads_session_id'), table_name='leads')
    op.drop_index(op.f('ix_leads_email'), table_name='leads')
    op.drop_index(op.f('ix_leads_contact_person_name'), table_name='leads')
    op.drop_index(op.f('ix_leads_company_name'), table_name='leads')
    op.drop_table('leads')
