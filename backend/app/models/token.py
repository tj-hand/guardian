"""
Guardian Token Model

6-digit authentication tokens for passwordless login.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Token(Base):
    """
    Token model for 6-digit authentication codes.

    Attributes:
        id: Unique token identifier
        user_id: Foreign key to user
        token_hash: SHA-256 hash of the token
        expires_at: Token expiration timestamp
        used_at: When token was used (None if unused)
        created_at: Token creation timestamp
    """

    __tablename__ = "guardian_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("guardian_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Token {self.id} for user {self.user_id}>"

    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)."""
        now = datetime.now(timezone.utc)
        return self.used_at is None and self.expires_at > now

    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def is_used(self) -> bool:
        """Check if token has been used."""
        return self.used_at is not None

    def mark_as_used(self) -> None:
        """Mark token as used."""
        self.used_at = datetime.now(timezone.utc)
