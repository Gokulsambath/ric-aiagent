"""Initial complete schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-01-07 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables with complete schema."""
    
    # Create users table first (referenced by other tables)
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_name'), 'users', ['name'], unique=False)
    
    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('org_name', sa.String(length=255), nullable=True),
        sa.Column('address', sa.String(length=300), nullable=True),
        sa.Column('city', sa.String(length=255), nullable=True),
        sa.Column('country', sa.String(length=125), nullable=True),
        sa.Column('contact_number', sa.String(length=25), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customers_name'), 'customers', ['name'], unique=False)
    op.create_index(op.f('ix_customers_email'), 'customers', ['email'], unique=False)
    
    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_sessions_user_id'), 'chat_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_chat_sessions_title'), 'chat_sessions', ['title'], unique=False)
    
    # Create chat_threads table
    op.create_table(
        'chat_threads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_threads_session_id'), 'chat_threads', ['session_id'], unique=False)
    op.create_index(op.f('ix_chat_threads_title'), 'chat_threads', ['title'], unique=False)
    
    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['thread_id'], ['chat_threads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_thread_id'), 'chat_messages', ['thread_id'], unique=False)
    
    # Create widget_config table
    op.create_table(
        'widget_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('tenant_name', sa.String(length=255), nullable=False),
        sa.Column('secret_key', sa.String(length=255), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('bot_id', sa.String(length=50), nullable=True),
        sa.Column('allowed_origins', sa.Text(), nullable=False, server_default=sa.text("'[\"*\"]'")),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id')
    )
    op.create_index('ix_widget_config_tenant_id', 'widget_config', ['tenant_id'])
    
    # Create acts table
    op.create_table(
        'acts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('state', sa.Text(), nullable=True),
        sa.Column('industry', sa.Text(), nullable=True),
        sa.Column('company_type', sa.Text(), nullable=True),
        sa.Column('legislative_area', sa.Text(), nullable=True),
        sa.Column('central_acts', sa.Text(), nullable=True),
        sa.Column('state_acts', sa.Text(), nullable=True),
        sa.Column('employee_applicability', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create session_data table
    op.create_table(
        'session_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('user_data', sa.JSON(), nullable=True),
        sa.Column('chat_history', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    
    # Create demos table
    op.create_table(
        'demos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('demo_date', sa.Date(), nullable=True),
        sa.Column('demo_time', sa.Time(), nullable=True),
        sa.Column('notes', sa.String(length=5000), nullable=True),
        sa.Column('participants', sa.JSON(), nullable=True),
        sa.Column('presenter', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_demos_title'), 'demos', ['title'], unique=False)
    op.create_index(op.f('ix_demos_status'), 'demos', ['status'], unique=False)
    op.create_index(op.f('ix_demos_customer_id'), 'demos', ['customer_id'], unique=False)
    
    # Create emails table
    op.create_table(
        'emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('message', sa.String(length=50000), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('customer_email', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_emails_subject'), 'emails', ['subject'], unique=False)
    op.create_index(op.f('ix_emails_customer_email'), 'emails', ['customer_email'], unique=False)
    
    # Create aiagents table
    op.create_table(
        'aiagents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('prompt', sa.String(length=250000), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for acts
    op.create_index('idx_state_industry', 'acts', ['state', 'industry'])
    op.create_index('idx_state_legislative_area', 'acts', ['state', 'legislative_area'])
    op.create_index('idx_industry_legislative_area', 'acts', ['industry', 'legislative_area'])
    op.create_index('idx_state_industry_legislative', 'acts', ['state', 'industry', 'legislative_area'])
    op.create_index(op.f('ix_acts_state'), 'acts', ['state'], unique=False)
    op.create_index(op.f('ix_acts_industry'), 'acts', ['industry'], unique=False)
    op.create_index(op.f('ix_acts_legislative_area'), 'acts', ['legislative_area'], unique=False)
    op.create_index(op.f('ix_acts_employee_applicability'), 'acts', ['employee_applicability'], unique=False)
    
    # Create indexes for session_data
    op.create_index(op.f('ix_session_data_session_id'), 'session_data', ['session_id'], unique=False)
    op.create_index(op.f('ix_session_data_created_at'), 'session_data', ['created_at'], unique=False)
    op.create_index(op.f('ix_session_data_is_active'), 'session_data', ['is_active'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    # Drop in reverse order to respect foreign key constraints
    op.drop_table('aiagents')
    op.drop_table('emails')
    op.drop_table('demos')
    op.drop_table('chat_messages')
    op.drop_table('chat_threads')
    op.drop_table('chat_sessions')
    op.drop_table('session_data')
    op.drop_table('acts')
    op.drop_table('widget_config')
    op.drop_table('customers')
    op.drop_table('users')