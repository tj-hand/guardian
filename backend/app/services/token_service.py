"""
Guardian Token Service

Token generation, validation, and management.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import generate_6_digit_token as gen_token, hash_token
from app.models.token import Token
from app.models.user import User

logger = logging.getLogger(__name__)


def generate_6_digit_token() -> str:
    """Generate a cryptographically secure 6-digit token."""
    return gen_token()


async def create_token_for_user(
    db: AsyncSession,
    user_id: str,
    token: str
) -> Token:
    """
    Create and store a hashed token for a user.

    Args:
        db: Database session
        user_id: User's UUID as string
        token: The 6-digit token to store (will be hashed)

    Returns:
        Token: The created token object
    """
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.token_expiry_minutes
    )

    db_token = Token(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at
    )

    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)

    logger.info(f"Token created for user {user_id}")
    return db_token


async def validate_token_for_user(
    db: AsyncSession,
    user_id: str,
    token: str
) -> Optional[Token]:
    """
    Validate a token for a specific user.

    Args:
        db: Database session
        user_id: User's UUID as string
        token: The 6-digit token to validate

    Returns:
        Token: The valid token object if validation succeeds
        None: If validation fails
    """
    token_hash = hash_token(token)

    result = await db.execute(
        select(Token)
        .where(Token.user_id == user_id)
        .where(Token.token_hash == token_hash)
        .where(Token.used_at.is_(None))
        .where(Token.expires_at > datetime.now(timezone.utc))
    )

    return result.scalar_one_or_none()


async def mark_token_as_used(db: AsyncSession, token: Token) -> None:
    """Mark a token as used to prevent reuse."""
    token.mark_as_used()
    await db.commit()
    await db.refresh(token)
    logger.info(f"Token {token.id} marked as used")


async def get_or_create_user_by_email(
    db: AsyncSession,
    email: str
) -> User:
    """
    Get existing user by email or create a new one.

    Args:
        db: Database session
        email: User's email address

    Returns:
        User: Existing or newly created user
    """
    email = email.lower().strip()

    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(email=email, is_active=True)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"New user created: {email}")
    else:
        logger.info(f"Existing user found: {email}")

    return user


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """
    Remove expired tokens from the database.

    Returns:
        int: Number of expired tokens deleted
    """
    result = await db.execute(
        delete(Token).where(Token.expires_at < datetime.now(timezone.utc))
    )
    await db.commit()

    count = result.rowcount
    logger.info(f"Cleaned up {count} expired tokens")
    return count


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get a user by email address.

    Args:
        db: Database session
        email: User's email address

    Returns:
        User: User object if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.email == email.lower().strip())
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    Get a user by ID.

    Args:
        db: Database session
        user_id: User's UUID as string

    Returns:
        User: User object if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
