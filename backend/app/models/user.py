"""
Guardian User Model

User accounts for authentication.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    """
    User model for Guardian authentication.

    Attributes:
        id: Unique user identifier (UUID)
        email: User email address (unique)
        is_active: Whether user can authenticate
        created_at: Account creation timestamp
        last_login: Last successful login timestamp
    """

    __tablename__ = "guardian_users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def update_last_login(self) -> None:
        """Update last login timestamp to now."""
        self.last_login = datetime.now(timezone.utc)
