"""Initial Guardian schema

Revision ID: 001
Revises:
Create Date: 2025-11-27

Creates the initial tables for Guardian authentication:
- guardian_users: User accounts
- guardian_tokens: 6-digit authentication tokens
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create guardian_users table
    op.create_table(
        'guardian_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_guardian_users_email', 'guardian_users', ['email'], unique=True)

    # Create guardian_tokens table
    op.create_table(
        'guardian_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['guardian_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_guardian_tokens_user_id', 'guardian_tokens', ['user_id'])
    op.create_index('ix_guardian_tokens_token_hash', 'guardian_tokens', ['token_hash'])


def downgrade() -> None:
    op.drop_index('ix_guardian_tokens_token_hash', table_name='guardian_tokens')
    op.drop_index('ix_guardian_tokens_user_id', table_name='guardian_tokens')
    op.drop_table('guardian_tokens')
    op.drop_index('ix_guardian_users_email', table_name='guardian_users')
    op.drop_table('guardian_users')
