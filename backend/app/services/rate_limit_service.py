"""
Rate limiting service for token requests.

This module implements rate limiting to prevent abuse of the token
generation system. Limits users to a configurable number of requests
within a time window.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.token import Token

logger = logging.getLogger(__name__)
settings = get_settings()


async def check_rate_limit(db: AsyncSession, user_id: str) -> Tuple[bool, int, int]:
    """
    Check if user has exceeded rate limit for token requests.

    Rate limit is based on token creation count within a time window.
    Configuration comes from settings:
    - rate_limit_requests: Max requests allowed (default: 3)
    - rate_limit_window_minutes: Time window in minutes (default: 15)

    Args:
        db: Database session
        user_id: User's UUID as string

    Returns:
        Tuple[bool, int, int]: (allowed, attempts_remaining, retry_after_seconds)
            - allowed: True if request is allowed, False if rate limited
            - attempts_remaining: Number of attempts remaining in current window
            - retry_after_seconds: Seconds until rate limit resets (0 if allowed)

    Example:
        >>> allowed, remaining, retry_after = await check_rate_limit(db, user_id)
        >>> if not allowed:
        ...     print(f"Rate limited. Retry after {retry_after} seconds")
        ... else:
        ...     print(f"{remaining} attempts remaining")
    """
    # Calculate time window
    window_start = datetime.now(timezone.utc) - timedelta(
        minutes=settings.rate_limit_window_minutes
    )

    # Count token requests in current window
    result = await db.execute(
        select(func.count(Token.id))
        .where(Token.user_id == user_id)
        .where(Token.created_at >= window_start)
    )

    request_count = result.scalar() or 0

    # Check if rate limit exceeded
    if request_count >= settings.rate_limit_requests:
        # Find oldest token in window to calculate retry_after
        oldest_token_result = await db.execute(
            select(Token.created_at)
            .where(Token.user_id == user_id)
            .where(Token.created_at >= window_start)
            .order_by(Token.created_at.asc())
            .limit(1)
        )

        oldest_token_time = oldest_token_result.scalar_one_or_none()

        if oldest_token_time:
            # Calculate when the oldest token will fall outside the window
            window_reset_time = oldest_token_time + timedelta(
                minutes=settings.rate_limit_window_minutes
            )
            retry_after_seconds = int(
                (window_reset_time - datetime.now(timezone.utc)).total_seconds()
            )

            # Ensure retry_after is at least 1 second
            retry_after_seconds = max(1, retry_after_seconds)
        else:
            # Fallback: full window duration
            retry_after_seconds = settings.rate_limit_window_minutes * 60

        logger.warning(
            f"Rate limit exceeded for user {user_id}. "
            f"Requests: {request_count}/{settings.rate_limit_requests}. "
            f"Retry after: {retry_after_seconds}s"
        )

        return False, 0, retry_after_seconds

    # Calculate remaining attempts
    attempts_remaining = settings.rate_limit_requests - request_count

    logger.info(
        f"Rate limit check passed for user {user_id}. "
        f"Requests: {request_count}/{settings.rate_limit_requests}. "
        f"Remaining: {attempts_remaining}"
    )

    return True, attempts_remaining, 0


async def check_rate_limit_by_email(db: AsyncSession, email: str) -> Tuple[bool, int, int]:
    """
    Check rate limit for an email address.

    This is a convenience wrapper that looks up the user by email
    and then checks the rate limit. If the user doesn't exist,
    the rate limit is checked as if they have no prior requests.

    Args:
        db: Database session
        email: User's email address

    Returns:
        Tuple[bool, int, int]: (allowed, attempts_remaining, retry_after_seconds)
            See check_rate_limit for details.

    Example:
        >>> allowed, remaining, retry_after = await check_rate_limit_by_email(
        ...     db, "user@example.com"
        ... )
    """
    from app.models.user import User

    # Try to find user by email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # If user doesn't exist, allow request (first time)
    if user is None:
        return True, settings.rate_limit_requests - 1, 0

    # Check rate limit for existing user
    return await check_rate_limit(db, str(user.id))


async def get_rate_limit_info(db: AsyncSession, user_id: str) -> dict:
    """
    Get detailed rate limit information for a user.

    Useful for debugging and monitoring.

    Args:
        db: Database session
        user_id: User's UUID as string

    Returns:
        dict: Rate limit information containing:
            - limit: Maximum requests allowed
            - window_minutes: Time window in minutes
            - current_count: Current request count in window
            - window_start: Start of current window (UTC)
            - is_limited: Whether user is currently rate limited

    Example:
        >>> info = await get_rate_limit_info(db, user_id)
        >>> print(f"User has made {info['current_count']}/{info['limit']} requests")
    """
    window_start = datetime.now(timezone.utc) - timedelta(
        minutes=settings.rate_limit_window_minutes
    )

    result = await db.execute(
        select(func.count(Token.id))
        .where(Token.user_id == user_id)
        .where(Token.created_at >= window_start)
    )

    request_count = result.scalar() or 0

    return {
        "limit": settings.rate_limit_requests,
        "window_minutes": settings.rate_limit_window_minutes,
        "current_count": request_count,
        "window_start": window_start.isoformat(),
        "is_limited": request_count >= settings.rate_limit_requests,
    }
