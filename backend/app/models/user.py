"""
User model for authentication system.

This module defines the User model representing users in the system.
Users authenticate via 6-digit email tokens.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """
    User model for passwordless authentication.

    Attributes:
        id: Unique identifier (UUID v4)
        email: User's email address (unique, used for token delivery)
        is_active: Whether the user account is active
        created_at: Timestamp of user creation (UTC)
        updated_at: Timestamp of last update (UTC)
        tokens: Relationship to Token model (one-to-many)
    """

    __tablename__ = "users"

    # Primary key - UUID v4 for global uniqueness
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique user identifier",
    )

    # Email address - unique constraint for authentication
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,  # Unique index for fast email lookups
        comment="User email address for authentication",
    )

    # Account status flag
    is_active = Column(
        Boolean, default=True, nullable=False, comment="Whether the user account is active"
    )

    # Timestamp fields with automatic updates
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="User creation timestamp (UTC)",
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp (UTC)",
    )

    # Relationship to tokens (one user can have many tokens)
    tokens = relationship(
        "Token",
        back_populates="user",
        cascade="all, delete-orphan",  # Delete tokens when user is deleted
        lazy="selectin",  # Efficient loading strategy
    )

    # Additional index for analytics queries
    __table_args__ = (
        Index("ix_users_created_at", "created_at"),
        {"comment": "Users table for passwordless authentication system"},
    )

    def __repr__(self) -> str:
        """String representation of User model."""
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return self.email
