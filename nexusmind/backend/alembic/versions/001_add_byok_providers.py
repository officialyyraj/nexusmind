"""Add BYOK provider connections.

Revision ID: 001
Revises: 
Create Date: 2026-07-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_provider_connections table for BYOK
    op.create_table(
        'user_provider_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('nickname', sa.String(100), nullable=True),
        sa.Column('encrypted_api_key', sa.Text(), nullable=False),
        sa.Column('base_url', sa.Text(), nullable=True),
        sa.Column('default_model', sa.String(100), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('last_verified', sa.DateTime(), nullable=True),
        sa.Column('verification_status', sa.String(20), nullable=True),
        sa.Column('verification_error', sa.Text(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('use_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'provider', 'nickname'),
    )
    
    # Create indexes for common queries
    op.create_index('idx_provider_user_id', 'user_provider_connections', ['user_id'])
    op.create_index('idx_provider_enabled', 'user_provider_connections', ['user_id', 'enabled'])
    op.create_index('idx_provider_default', 'user_provider_connections', ['user_id', 'is_default'])
    
    # Create audit log table
    op.create_table(
        'provider_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('details', postgresql.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    
    op.create_index('idx_audit_user', 'provider_audit_log', ['user_id'])
    op.create_index('idx_audit_connection', 'provider_audit_log', ['connection_id'])
    op.create_index('idx_audit_action', 'provider_audit_log', ['action'])
    op.create_index('idx_audit_created', 'provider_audit_log', ['created_at'])
    
    # Update existing llm_providers table if exists
    # This is optional - we keep it for system-wide providers
    # User providers go to user_provider_connections


def downgrade() -> None:
    op.drop_index('idx_audit_created', table_name='provider_audit_log')
    op.drop_index('idx_audit_action', table_name='provider_audit_log')
    op.drop_index('idx_audit_connection', table_name='provider_audit_log')
    op.drop_index('idx_audit_user', table_name='provider_audit_log')
    op.drop_table('provider_audit_log')
    
    op.drop_index('idx_provider_default', table_name='user_provider_connections')
    op.drop_index('idx_provider_enabled', table_name='user_provider_connections')
    op.drop_index('idx_provider_user_id', table_name='user_provider_connections')
    op.drop_table('user_provider_connections')
