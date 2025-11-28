"""
JWT (JSON Web Token) service for session management.

This module provides JWT token creation, validation, and decoding for
authenticated user sessions. Tokens are signed using HS256 algorithm
and contain user identity claims.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt

from app.core.config import get_settings
from app.models.user import User


def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token for authenticated user.

    The token payload contains:
    - sub: User ID (UUID as string) - standard JWT subject claim
    - email: User's email address
    - exp: Expiration timestamp (Unix timestamp)
    - iat: Issued at timestamp (Unix timestamp)

    Args:
        user: Authenticated user object
        expires_delta: Optional custom expiration duration. If not provided,
                       uses SESSION_EXPIRY_DAYS from settings (default 7 days)

    Returns:
        str: Encoded JWT token string

    Raises:
        JWTError: If token encoding fails

    Example:
        >>> from datetime import timedelta
        >>> token = create_access_token(user)  # Default 7 days
        >>> token = create_access_token(user, timedelta(hours=1))  # Custom expiry
    """
    settings = get_settings()

    # Calculate expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.session_expiry_days)

    # Build JWT payload with standard claims
    payload = {
        "sub": str(user.id),  # Subject: user ID
        "email": user.email,  # Custom claim: email
        "exp": expire,  # Expiration time
        "iat": datetime.now(timezone.utc),  # Issued at
    }

    # Encode token using secret key and HS256 algorithm
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token.

    Verifies:
    - Token signature is valid
    - Token has not expired
    - Token structure is correct

    Args:
        token: JWT token string to decode

    Returns:
        Dict[str, Any]: Decoded token payload containing claims

    Raises:
        JWTError: If token is invalid, expired, or malformed
        ExpiredSignatureError: If token has expired (subclass of JWTError)
        JWTClaimsError: If claims validation fails (subclass of JWTError)

    Example:
        >>> try:
        ...     payload = decode_access_token(token)
        ...     user_id = payload.get("sub")
        ... except JWTError:
        ...     print("Invalid token")
    """
    settings = get_settings()

    # Decode and validate token
    # This will automatically check signature and expiration
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    return payload


def verify_token(token: str) -> Optional[str]:
    """
    Verify JWT token and extract user ID.

    This is a convenience wrapper around decode_access_token that:
    1. Attempts to decode the token
    2. Extracts the user ID from the "sub" claim
    3. Returns None if any validation fails

    Args:
        token: JWT token string to verify

    Returns:
        str: User ID (UUID as string) if token is valid
        None: If token is invalid, expired, or missing user ID

    Example:
        >>> user_id = verify_token(token)
        >>> if user_id:
        ...     # Token is valid, proceed with authentication
        ...     user = await get_user_by_id(user_id)
        ... else:
        ...     # Token is invalid
        ...     raise HTTPException(status_code=401)
    """
    try:
        payload = decode_access_token(token)

        # Extract user ID from "sub" claim
        user_id = payload.get("sub")

        if user_id is None:
            return None

        return str(user_id)

    except JWTError:
        # Token is invalid, expired, or malformed
        return None


def get_token_expiry_seconds() -> int:
    """
    Get JWT token expiry duration in seconds.

    Returns:
        int: Number of seconds until token expires

    Example:
        >>> expiry = get_token_expiry_seconds()
        >>> print(f"Token valid for {expiry} seconds")
    """
    settings = get_settings()
    return settings.session_expiry_days * 24 * 60 * 60
