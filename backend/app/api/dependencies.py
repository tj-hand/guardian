"""
FastAPI dependencies for authentication and authorization.

This module provides dependency injection functions for:
- Extracting and validating JWT tokens from requests
- Loading authenticated user from database
- Protecting routes that require authentication
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import jwt_service
from app.models.user import User


# HTTPBearer security scheme for JWT tokens
# This extracts the token from Authorization: Bearer <token> header
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.

    This dependency:
    1. Extracts JWT token from Authorization header
    2. Validates token signature and expiration
    3. Extracts user ID from token claims
    4. Loads user from database
    5. Verifies user exists and is active

    Args:
        credentials: HTTP Bearer credentials containing JWT token (auto-extracted)
        db: Database session (injected)

    Returns:
        User: Authenticated user object

    Raises:
        HTTPException 401: If token is invalid, expired, or user not found/inactive

    Example:
        @router.get("/protected")
        async def protected_route(
            current_user: User = Depends(get_current_user)
        ):
            return {"user_id": current_user.id}
    """
    # Extract token from credentials
    token = credentials.credentials

    # Verify token and extract user ID
    user_id = jwt_service.verify_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Load user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user (additional validation layer).

    This is an additional layer on top of get_current_user that explicitly
    checks the is_active flag. While get_current_user already checks this,
    having this separate dependency makes the intent explicit and allows
    for future extension (e.g., checking email verification, subscription status).

    Args:
        current_user: Authenticated user (from get_current_user dependency)

    Returns:
        User: Active authenticated user

    Raises:
        HTTPException 403: If user account is not active

    Example:
        @router.get("/premium")
        async def premium_route(
            user: User = Depends(get_current_active_user)
        ):
            return {"status": "premium"}
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get current user if authenticated, None otherwise.

    This is useful for routes that can work with or without authentication,
    showing different data based on authentication status.

    Args:
        credentials: Optional HTTP Bearer credentials (auto-extracted)
        db: Database session (injected)

    Returns:
        User: Authenticated user if token is valid
        None: If no token provided or token is invalid

    Example:
        @router.get("/public")
        async def public_route(
            user: Optional[User] = Depends(get_optional_current_user)
        ):
            if user:
                return {"message": f"Hello {user.email}"}
            return {"message": "Hello guest"}
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        user_id = jwt_service.verify_token(token)

        if user_id is None:
            return None

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            return None

        return user

    except Exception:
        # Silently fail for optional authentication
        return None
