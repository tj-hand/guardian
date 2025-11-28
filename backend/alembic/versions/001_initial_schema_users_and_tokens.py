"""
Initial schema: users and tokens tables

Migration: 001_initial_schema_users_and_tokens
Created: 2025-11-05
Description: Creates the initial database schema for passwordless authentication
             system with users and 6-digit email tokens.

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-11-05 14:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Apply migration: Create users and tokens tables.

    This migration creates:
    1. users table - stores user accounts with email-based authentication
    2. tokens table - stores 6-digit authentication tokens with expiration

    All tables use UUID primary keys for global uniqueness.
    Timestamps are timezone-aware (UTC).
    """

    # Create users table
    op.create_table(
        'users',
        # Primary key - UUID v4
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Unique user identifier'
        ),
        # Email address - unique constraint for authentication
        sa.Column(
            'email',
            sa.String(length=255),
            nullable=False,
            comment='User email address for authentication'
        ),
        # Account status flag
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default='true',
            comment='Whether the user account is active'
        ),
        # Timestamp fields with automatic updates
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
            comment='User creation timestamp (UTC)'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
            comment='Last update timestamp (UTC)'
        ),
        # Primary key constraint
        sa.PrimaryKeyConstraint('id'),
        # Unique constraint on email
        sa.UniqueConstraint('email', name='uq_users_email'),
        comment='Users table for passwordless authentication system'
    )

    # Create indexes on users table
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_created_at', 'users', ['created_at'], unique=False)

    # Create tokens table
    op.create_table(
        'tokens',
        # Primary key - UUID v4
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Unique token identifier'
        ),
        # Foreign key to users table with CASCADE delete
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to the user who owns this token'
        ),
        # SHA-256 hash of the 6-digit token (64 characters)
        sa.Column(
            'token_hash',
            sa.String(length=64),
            nullable=False,
            comment='SHA-256 hash of the 6-digit authentication token'
        ),
        # Expiration timestamp - tokens are typically valid for 15 minutes
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=False,
            comment='Token expiration timestamp (UTC)'
        ),
        # Usage timestamp - NULL means token hasn't been used yet
        sa.Column(
            'used_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Timestamp when token was used (NULL if unused)'
        ),
        # Creation timestamp
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
            comment='Token creation timestamp (UTC)'
        ),
        # Primary key constraint
        sa.PrimaryKeyConstraint('id'),
        # Foreign key constraint with CASCADE delete
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            name='fk_tokens_user_id_users',
            ondelete='CASCADE'
        ),
        # Check constraint: expiration must be after creation
        sa.CheckConstraint(
            'expires_at > created_at',
            name='check_expires_at_after_created_at'
        ),
        comment='Authentication tokens table for 6-digit email codes'
    )

    # Create indexes on tokens table
    # Critical index for fast token validation lookups
    op.create_index('ix_tokens_token_hash', 'tokens', ['token_hash'], unique=False)

    # Index for user token history queries
    op.create_index('ix_tokens_user_id', 'tokens', ['user_id'], unique=False)

    # Index for cleanup queries (finding expired tokens)
    op.create_index('ix_tokens_expires_at', 'tokens', ['expires_at'], unique=False)

    # Composite index for common query pattern (unused + not expired)
    # This optimizes the most frequent query: finding valid tokens by hash
    op.create_index(
        'ix_tokens_validation',
        'tokens',
        ['token_hash', 'expires_at', 'used_at'],
        unique=False
    )


def downgrade() -> None:
    """
    Revert migration: Drop users and tokens tables.

    This will drop both tables and all associated indexes.
    CASCADE will handle the foreign key relationships.
    """

    # Drop tokens table first (has foreign key to users)
    op.drop_index('ix_tokens_validation', table_name='tokens')
    op.drop_index('ix_tokens_expires_at', table_name='tokens')
    op.drop_index('ix_tokens_user_id', table_name='tokens')
    op.drop_index('ix_tokens_token_hash', table_name='tokens')
    op.drop_table('tokens')

    # Drop users table
    op.drop_index('ix_users_created_at', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
