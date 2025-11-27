"""
Guardian Authentication Routes

API endpoints for passwordless 6-digit token authentication.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import mask_email
from app.models.user import User
from app.schemas.auth import (
    LogoutResponse,
    TokenRequest,
    TokenRequestResponse,
    TokenValidation,
    TokenValidationResponse,
    UserResponse,
)
from app.services import (
    check_rate_limit_by_email,
    create_token_for_user,
    generate_6_digit_token,
    get_or_create_user_by_email,
    mark_token_as_used,
    send_token_email,
    validate_token_for_user,
)
from app.services.jwt_service import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/request-token",
    response_model=TokenRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Request 6-digit authentication token",
    description="Request a 6-digit token to be sent via email. Rate limited.",
    responses={
        200: {"description": "Token request accepted"},
        429: {"description": "Rate limit exceeded"},
    }
)
async def request_token(
    request: TokenRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenRequestResponse:
    """
    Request a 6-digit authentication token via email.

    Security:
    - Always returns 200 to prevent email enumeration
    - Rate limited to prevent abuse
    - Tokens are one-time use and expire quickly
    """
    email = request.email
    logger.info(f"Token request received for: {mask_email(email)}")

    try:
        # Check rate limit
        allowed, attempts_remaining, retry_after = await check_rate_limit_by_email(
            db, email
        )

        if not allowed:
            logger.warning(f"Rate limit exceeded for {mask_email(email)}")
            minutes = retry_after // 60
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "detail": f"Too many requests. Please try again in {minutes} minutes.",
                    "retry_after": retry_after,
                    "attempts_remaining": 0
                }
            )

        # Check email whitelist if enabled
        if settings.enable_email_whitelist:
            result = await db.execute(
                select(User).where(User.email == email.lower())
            )
            existing_user = result.scalar_one_or_none()

            if not existing_user:
                logger.warning(f"Whitelist rejection: {mask_email(email)}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Email not authorized. Contact administrator."
                )

        # Get or create user
        user = await get_or_create_user_by_email(db, email)

        # Generate token
        token = generate_6_digit_token()
        logger.info(f"Generated token for user {user.id}")

        # Store hashed token
        await create_token_for_user(db, str(user.id), token)

        # Send email
        await send_token_email(email, token)

        return TokenRequestResponse(
            message="If the email exists, a 6-digit code has been sent",
            email=mask_email(email),
            expires_in_minutes=settings.token_expiry_minutes
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error processing token request: {e}", exc_info=True)
        # Still return success for security
        return TokenRequestResponse(
            message="If the email exists, a 6-digit code has been sent",
            email=mask_email(email),
            expires_in_minutes=settings.token_expiry_minutes
        )


@router.post(
    "/validate-token",
    response_model=TokenValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate 6-digit token",
    description="Validate token and receive JWT session.",
    responses={
        200: {"description": "Token valid, JWT created"},
        401: {"description": "Invalid or expired token"},
    }
)
async def validate_token(
    request: TokenValidation,
    db: AsyncSession = Depends(get_db)
) -> TokenValidationResponse:
    """
    Validate 6-digit token and create JWT session.
    """
    logger.info(f"Token validation for: {mask_email(request.email)}")

    # Find user
    result = await db.execute(
        select(User).where(User.email == request.email.lower())
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"User not found: {mask_email(request.email)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or token"
        )

    # Validate token
    token_obj = await validate_token_for_user(
        db, str(user.id), request.token
    )

    if not token_obj:
        logger.warning(f"Invalid token for user {user.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Mark token as used
    await mark_token_as_used(db, token_obj)

    # Update last login
    user.update_last_login()
    await db.commit()

    # Create JWT
    access_token = create_access_token(user)
    expires_in_seconds = settings.session_expiry_days * 24 * 60 * 60

    logger.info(f"User {user.id} authenticated successfully")

    return TokenValidationResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active
        )
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get authenticated user information.",
    responses={
        200: {"description": "User information"},
        401: {"description": "Not authenticated"},
    }
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current authenticated user information."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        created_at=current_user.created_at,
        is_active=current_user.is_active
    )


@router.post(
    "/refresh",
    response_model=TokenValidationResponse,
    summary="Refresh JWT token",
    description="Get a new JWT token before the current one expires.",
    responses={
        200: {"description": "New JWT created"},
        401: {"description": "Not authenticated"},
    }
)
async def refresh_token(
    current_user: User = Depends(get_current_user)
) -> TokenValidationResponse:
    """Refresh JWT token to extend session."""
    access_token = create_access_token(current_user)
    expires_in_seconds = settings.session_expiry_days * 24 * 60 * 60

    logger.info(f"JWT refreshed for user {current_user.id}")

    return TokenValidationResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
        user=UserResponse(
            id=str(current_user.id),
            email=current_user.email,
            created_at=current_user.created_at,
            is_active=current_user.is_active
        )
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout user",
    description="Logout user. Client should discard the JWT token.",
    responses={
        200: {"description": "Logout successful"},
        401: {"description": "Not authenticated"},
    }
)
async def logout(
    current_user: User = Depends(get_current_user)
) -> LogoutResponse:
    """
    Logout user.

    Note: JWT is stateless, so logout is primarily client-side.
    This endpoint confirms the action.
    """
    logger.info(f"User {current_user.id} logged out")
    return LogoutResponse(message="Successfully logged out")
