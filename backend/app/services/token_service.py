"""
Token generation and validation service.

This module provides cryptographically secure 6-digit token generation,
hashing, storage, and validation for email authentication.
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.token import Token
from app.core.config import get_settings


settings = get_settings()


def generate_6_digit_token() -> str:
    """
    Generate a cryptographically secure 6-digit numeric token.

    Uses Python's secrets module for cryptographic randomness.
    Token range: 000000 to 999999 (1,000,000 possible combinations).

    Returns:
        str: Zero-padded 6-digit token string (e.g., "000123", "456789")

    Example:
        >>> token = generate_6_digit_token()
        >>> len(token)
        6
        >>> token.isdigit()
        True
    """
    # Generate random number from 0 to 999999
    token = secrets.randbelow(1000000)

    # Zero-pad to ensure exactly 6 digits
    return f"{token:06d}"


def hash_token(token: str) -> str:
    """
    Hash a token using SHA-256 for secure storage.

    Args:
        token: The 6-digit token string to hash

    Returns:
        str: Hexadecimal SHA-256 hash of the token (64 characters)

    Example:
        >>> hash_token("123456")
        '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92'
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


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
        Token: The created token database object

    Raises:
        SQLAlchemyError: If database operation fails

    Example:
        >>> token_obj = await create_token_for_user(db, user_id, "123456")
        >>> token_obj.is_valid()
        True
    """
    # Hash the token before storage
    token_hash = hash_token(token)

    # Calculate expiration time
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.token_expiry_minutes
    )

    # Create token object
    db_token = Token(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at
    )

    # Add to database
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)

    return db_token


async def validate_token_for_user(
    db: AsyncSession,
    user_id: str,
    token: str
) -> Optional[Token]:
    """
    Validate a token for a specific user.

    Checks:
    1. Token hash matches stored hash
    2. Token hasn't been used yet
    3. Token hasn't expired

    Args:
        db: Database session
        user_id: User's UUID as string
        token: The 6-digit token to validate

    Returns:
        Token: The valid token object if validation succeeds
        None: If validation fails (invalid, used, or expired)

    Example:
        >>> token_obj = await validate_token_for_user(db, user_id, "123456")
        >>> if token_obj:
        ...     print("Token is valid")
        ... else:
        ...     print("Token is invalid")
    """
    # Hash the provided token
    token_hash = hash_token(token)

    # Find matching token for this user
    result = await db.execute(
        select(Token)
        .where(Token.user_id == user_id)
        .where(Token.token_hash == token_hash)
        .where(Token.used_at.is_(None))  # Token not used yet
        .where(Token.expires_at > datetime.now(timezone.utc))  # Not expired
    )

    db_token = result.scalar_one_or_none()

    return db_token


async def mark_token_as_used(
    db: AsyncSession,
    token: Token
) -> None:
    """
    Mark a token as used to prevent reuse.

    Args:
        db: Database session
        token: Token object to mark as used

    Raises:
        SQLAlchemyError: If database operation fails

    Example:
        >>> token_obj = await validate_token_for_user(db, user_id, "123456")
        >>> if token_obj:
        ...     await mark_token_as_used(db, token_obj)
    """
    token.mark_as_used()
    await db.commit()
    await db.refresh(token)


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """
    Remove expired tokens from the database.

    This is a maintenance operation that should be run periodically
    (e.g., via cron job or scheduled task) to prevent database bloat.

    Args:
        db: Database session

    Returns:
        int: Number of expired tokens deleted

    Example:
        >>> deleted_count = await cleanup_expired_tokens(db)
        >>> print(f"Removed {deleted_count} expired tokens")
    """
    # Delete all expired tokens
    result = await db.execute(
        delete(Token)
        .where(Token.expires_at < datetime.now(timezone.utc))
    )

    await db.commit()

    return result.rowcount


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
        User: Existing or newly created user object

    Raises:
        SQLAlchemyError: If database operation fails

    Example:
        >>> user = await get_or_create_user_by_email(db, "user@example.com")
        >>> print(user.email)
        user@example.com
    """
    # Try to find existing user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    # Create new user if doesn't exist
    if user is None:
        user = User(email=email, is_active=True)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user
