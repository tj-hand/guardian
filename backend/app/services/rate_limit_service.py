"""
Guardian Rate Limit Service

Rate limiting for token requests to prevent abuse.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.token import Token
from app.models.user import User

logger = logging.getLogger(__name__)


async def check_rate_limit_by_email(
    db: AsyncSession,
    email: str
) -> Tuple[bool, int, int]:
    """
    Check if an email address has exceeded the rate limit.

    Args:
        db: Database session
        email: Email address to check

    Returns:
        Tuple of:
        - allowed: Whether the request is allowed
        - attempts_remaining: Number of attempts left in window
        - retry_after: Seconds until rate limit resets (0 if allowed)
    """
    email = email.lower().strip()
    window_start = datetime.now(timezone.utc) - timedelta(
        minutes=settings.rate_limit_window_minutes
    )

    # Find user first
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user is None:
        # New user - no rate limit history
        return True, settings.rate_limit_requests - 1, 0

    # Count recent token requests
    result = await db.execute(
        select(func.count(Token.id))
        .where(Token.user_id == user.id)
        .where(Token.created_at >= window_start)
    )
    request_count = result.scalar() or 0

    if request_count >= settings.rate_limit_requests:
        # Rate limited - calculate retry time
        result = await db.execute(
            select(Token.created_at)
            .where(Token.user_id == user.id)
            .where(Token.created_at >= window_start)
            .order_by(Token.created_at.asc())
            .limit(1)
        )
        oldest_token_time = result.scalar_one_or_none()

        if oldest_token_time:
            retry_after = int(
                (oldest_token_time + timedelta(minutes=settings.rate_limit_window_minutes)
                 - datetime.now(timezone.utc)).total_seconds()
            )
            retry_after = max(0, retry_after)
        else:
            retry_after = settings.rate_limit_window_minutes * 60

        logger.warning(f"Rate limit exceeded for {email}: {request_count} requests")
        return False, 0, retry_after

    attempts_remaining = settings.rate_limit_requests - request_count - 1
    return True, attempts_remaining, 0


async def get_recent_request_count(
    db: AsyncSession,
    user_id: str,
    window_minutes: int = None
) -> int:
    """
    Get the count of recent token requests for a user.

    Args:
        db: Database session
        user_id: User's UUID
        window_minutes: Time window in minutes (default from settings)

    Returns:
        int: Number of requests in the window
    """
    if window_minutes is None:
        window_minutes = settings.rate_limit_window_minutes

    window_start = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

    result = await db.execute(
        select(func.count(Token.id))
        .where(Token.user_id == user_id)
        .where(Token.created_at >= window_start)
    )

    return result.scalar() or 0
