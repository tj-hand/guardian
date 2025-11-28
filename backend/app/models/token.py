"""
Token model for 6-digit email authentication.

This module defines the Token model for storing 6-digit authentication tokens
sent via email. Tokens are hashed for security and expire after 15 minutes.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Token(Base):
    """
    Token model for 6-digit email authentication.

    Tokens are one-time use codes with expiration. The actual 6-digit token
    is hashed using SHA-256 before storage for security.

    Attributes:
        id: Unique identifier (UUID v4)
        user_id: Foreign key to users table
        token_hash: SHA-256 hash of the 6-digit token
        expires_at: Expiration timestamp (UTC, typically 15 minutes from creation)
        used_at: Timestamp when token was used (NULL if unused)
        created_at: Token creation timestamp (UTC)
        user: Relationship to User model (many-to-one)
    """

    __tablename__ = "tokens"

    # Primary key - UUID v4
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique token identifier",
    )

    # Foreign key to users table with CASCADE delete
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Index for user token history queries
        comment="Reference to the user who owns this token",
    )

    # SHA-256 hash of the 6-digit token (64 characters)
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,  # Critical index for fast token validation lookups
        comment="SHA-256 hash of the 6-digit authentication token",
    )

    # Expiration timestamp - tokens are typically valid for 15 minutes
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,  # Index for cleanup queries (finding expired tokens)
        comment="Token expiration timestamp (UTC)",
    )

    # Usage timestamp - NULL means token hasn't been used yet
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when token was used (NULL if unused)",
    )

    # Creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Token creation timestamp (UTC)",
    )

    # Relationship to user (many tokens belong to one user)
    user: Mapped["User"] = relationship("User", back_populates="tokens")

    # Table constraints and indexes
    __table_args__ = (
        # Check constraint: expiration must be after creation
        CheckConstraint("expires_at > created_at", name="check_expires_at_after_created_at"),
        # Composite index for common query pattern (unused + not expired)
        # Note: Single-column indexes for token_hash, user_id, and expires_at are
        # created automatically via index=True on their column definitions above
        Index("ix_tokens_validation", "token_hash", "expires_at", "used_at"),
        {"comment": "Authentication tokens table for 6-digit email codes"},
    )

    def __repr__(self) -> str:
        """String representation of Token model."""
        return (
            f"<Token(id={self.id}, user_id={self.user_id}, "
            f"expires_at={self.expires_at}, used={self.used_at is not None})>"
        )

    def is_valid(self) -> bool:
        """
        Check if token is still valid (not expired and not used).

        Returns:
            bool: True if token can be used, False otherwise

        Note:
            This method checks local state only. Always verify against
            database timestamp for accurate expiration checking.
        """
        from datetime import datetime, timezone

        if self.used_at is not None:
            return False  # Token already used

        if self.expires_at < datetime.now(timezone.utc):
            return False  # Token expired

        return True

    def mark_as_used(self) -> None:
        """
        Mark token as used by setting used_at timestamp.

        This method sets the timestamp but does NOT commit to database.
        The caller must commit the session.
        """
        from datetime import datetime, timezone

        self.used_at = datetime.now(timezone.utc)
