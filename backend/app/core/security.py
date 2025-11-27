"""
Guardian Security Utilities

JWT token handling, password hashing, and cryptographic utilities.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings


def generate_6_digit_token() -> str:
    """
    Generate a cryptographically secure 6-digit numeric token.

    Returns:
        str: Zero-padded 6-digit token (e.g., "000123", "456789")
    """
    token = secrets.randbelow(1000000)
    return f"{token:06d}"


def hash_token(token: str) -> str:
    """
    Hash a token using SHA-256 for secure storage.

    Args:
        token: The token string to hash

    Returns:
        str: Hexadecimal SHA-256 hash (64 characters)
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token_hash(token: str, token_hash: str) -> bool:
    """
    Verify a token against its hash.

    Args:
        token: The plaintext token
        token_hash: The stored hash to verify against

    Returns:
        bool: True if token matches hash
    """
    return hash_token(token) == token_hash


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: Token subject (usually user ID)
        expires_delta: Custom expiration time
        additional_claims: Extra claims to include in token

    Returns:
        str: Encoded JWT token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.session_expiry_days)

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }

    if additional_claims:
        to_encode.update(additional_claims)

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token.

    Args:
        token: The JWT token to decode

    Returns:
        dict: Decoded token payload if valid
        None: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except ExpiredSignatureError:
        return None
    except InvalidTokenError:
        return None


def mask_email(email: str) -> str:
    """
    Mask an email address for privacy.

    Examples:
        - "user@example.com" -> "u***@example.com"
        - "a@example.com" -> "a***@example.com"

    Args:
        email: Email address to mask

    Returns:
        str: Masked email address
    """
    if "@" not in email:
        return "***"

    username, domain = email.split("@", 1)

    if len(username) <= 1:
        return f"{username}***@{domain}"

    return f"{username[0]}***@{domain}"
