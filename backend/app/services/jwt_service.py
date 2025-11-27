"""
Guardian JWT Service

JWT token creation and validation.
"""

import logging
from datetime import timedelta
from typing import Optional

from app.core.config import settings
from app.core.security import create_access_token as create_token, decode_access_token as decode_token
from app.models.user import User

logger = logging.getLogger(__name__)


def create_access_token(user: User, additional_claims: Optional[dict] = None) -> str:
    """
    Create a JWT access token for a user.

    Args:
        user: User to create token for
        additional_claims: Optional extra claims

    Returns:
        str: Encoded JWT token
    """
    claims = {
        "email": user.email,
        "is_active": user.is_active,
    }

    if additional_claims:
        claims.update(additional_claims)

    token = create_token(
        subject=str(user.id),
        expires_delta=timedelta(days=settings.session_expiry_days),
        additional_claims=claims
    )

    logger.info(f"JWT created for user {user.id}")
    return token


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        dict: Token payload if valid, None otherwise
    """
    return decode_token(token)


def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from a JWT token.

    Args:
        token: JWT token

    Returns:
        str: User ID if valid, None otherwise
    """
    payload = decode_token(token)
    if payload:
        return payload.get("sub")
    return None


def is_token_valid(token: str) -> bool:
    """
    Check if a JWT token is valid.

    Args:
        token: JWT token to check

    Returns:
        bool: True if valid, False otherwise
    """
    return decode_token(token) is not None
