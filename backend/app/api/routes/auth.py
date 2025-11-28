"""
Authentication routes for token generation and validation.

This module provides API endpoints for:
- Requesting 6-digit authentication tokens via email
- Validating tokens (to be implemented in future story)
- Session management (to be implemented in future story)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LogoutResponse,
    RateLimitError,
    TokenRequest,
    TokenRequestResponse,
    TokenValidation,
    TokenValidationResponse,
    UserResponse,
)
from app.services import email_service, jwt_service, rate_limit_service, token_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/request-token",
    response_model=TokenRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Request 6-digit authentication token",
    description=(
        "Request a 6-digit authentication token to be sent via email. "
        "Rate limited to 3 requests per email per 15 minutes."
    ),
    responses={
        200: {
            "description": "Token request accepted (email sent if user exists)",
            "model": TokenRequestResponse,
        },
        429: {"description": "Rate limit exceeded", "model": RateLimitError},
        500: {"description": "Server error"},
    },
)
async def request_token(
    request: TokenRequest, db: AsyncSession = Depends(get_db)
) -> TokenRequestResponse:
    """
    Request a 6-digit authentication token via email.

    Security Design:
    - Always returns success (200) to prevent email enumeration
    - Masks email address in response (e.g., "u***@example.com")
    - Rate limiting prevents abuse
    - Tokens are one-time use and expire in 15 minutes

    Args:
        request: Token request containing email address
        db: Database session (injected)

    Returns:
        TokenRequestResponse: Success message with masked email

    Raises:
        HTTPException 429: Rate limit exceeded
        HTTPException 500: Server error

    Example:
        POST /api/auth/request-token
        {
            "email": "user@example.com"
        }

        Response:
        {
            "message": "If the email exists, a 6-digit code has been sent",
            "email": "u***@example.com",
            "expires_in_minutes": 15
        }
    """
    email = request.email

    logger.info(f"Token request received for email: {_mask_email(email)}")

    try:
        # Step 1: Check rate limit BEFORE any other operations
        # This prevents abuse and protects against enumeration attacks
        rate_check = await rate_limit_service.check_rate_limit_by_email(db, email)
        allowed, attempts_remaining, retry_after = rate_check

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {_mask_email(email)}. "
                f"Retry after {retry_after} seconds"
            )
            minutes = retry_after // 60
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "detail": (f"Too many requests. Please try again in " f"{minutes} minutes."),
                    "retry_after": retry_after,
                    "attempts_remaining": 0,
                },
            )

        # Step 2: Check email whitelist if enabled
        from app.core.config import get_settings

        settings = get_settings()

        if settings.enable_email_whitelist:
            # Whitelist enabled - check if user exists
            from sqlalchemy import select

            result = await db.execute(select(User).where(User.email == email.lower()))
            existing_user = result.scalar_one_or_none()

            if not existing_user:
                logger.warning(f"Whitelist rejection: {_mask_email(email)} not in " f"users table")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "Email not authorized. Please contact your "
                        "administrator to request access."
                    ),
                )

        # Step 3: Get or create user
        # If whitelist is enabled, user already exists (verified above)
        # If whitelist is disabled, create user if doesn't exist
        user = await token_service.get_or_create_user_by_email(db, email)

        # Step 4: Generate 6-digit token
        token = token_service.generate_6_digit_token()
        logger.info(f"Generated token for user {user.id}")

        # Step 5: Store hashed token in database
        await token_service.create_token_for_user(db, str(user.id), token)
        logger.info(f"Token stored for user {user.id}")

        # Step 6: Send email asynchronously (don't wait for completion)
        # We don't await because we don't want to reveal send status
        # Email service always returns True for security
        await email_service.send_token_email(email, token)

        # Step 7: Return success response
        # Always return the same message regardless of whether user exists
        # This prevents email enumeration attacks
        settings = get_settings()

        return TokenRequestResponse(
            message="If the email exists, a 6-digit code has been sent",
            email=_mask_email(email),
            expires_in_minutes=settings.token_expiry_minutes,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like rate limit)
        raise

    except Exception as e:
        # Log error but don't expose details to client
        logger.error(
            f"Error processing token request for {_mask_email(email)}: {str(e)}", exc_info=True
        )

        # Still return success for security (don't reveal errors)
        # In a real attack scenario, errors shouldn't reveal system state
        from app.core.config import get_settings

        settings = get_settings()

        return TokenRequestResponse(
            message="If the email exists, a 6-digit code has been sent",
            email=_mask_email(email),
            expires_in_minutes=settings.token_expiry_minutes,
        )


@router.post(
    "/validate-token",
    response_model=TokenValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate 6-digit token and create session",
    description=(
        "Validate a 6-digit token and create a JWT session. "
        "Token must be valid, not expired, and not already used."
    ),
    responses={
        200: {"description": "Token valid, JWT session created", "model": TokenValidationResponse},
        401: {"description": "Invalid or expired token"},
    },
)
async def validate_token(
    request: TokenValidation, db: AsyncSession = Depends(get_db)
) -> TokenValidationResponse:
    """
    Validate 6-digit token and create JWT session.

    Workflow:
    1. Verify user exists by email
    2. Validate token (hash match, not used, not expired)
    3. Mark token as used (one-time use)
    4. Create JWT access token
    5. Return JWT and user information

    Args:
        request: Token validation request (email + 6-digit token)
        db: Database session (injected)

    Returns:
        TokenValidationResponse: JWT token and user info

    Raises:
        HTTPException 401: If email or token is invalid

    Example:
        POST /api/auth/validate-token
        {
            "email": "user@example.com",
            "token": "123456"
        }

        Response:
        {
            "access_token": "eyJhbGc...",
            "token_type": "bearer",
            "expires_in": 604800,
            "user": {...}
        }
    """
    from sqlalchemy import select

    from app.core.config import get_settings

    logger.info(f"Token validation request for email: {_mask_email(request.email)}")

    # Step 1: Find user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"Token validation failed: user not found for {_mask_email(request.email)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or token"
        )

    # Step 2: Validate token
    token_obj = await token_service.validate_token_for_user(db, str(user.id), request.token)

    if not token_obj:
        logger.warning(f"Token validation failed: invalid token for user {user.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    # Step 3: Mark token as used
    await token_service.mark_token_as_used(db, token_obj)
    logger.info(f"Token marked as used for user {user.id}")

    # Step 4: Create JWT access token
    access_token = jwt_service.create_access_token(user)
    logger.info(f"JWT created for user {user.id}")

    # Step 5: Return response with JWT and user info
    settings = get_settings()
    expires_in_seconds = settings.session_expiry_days * 24 * 60 * 60

    return TokenValidationResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
        user=UserResponse(
            id=str(user.id), email=user.email, created_at=user.created_at, is_active=user.is_active
        ),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user information",
    description="Get information about the currently authenticated user.",
    responses={
        200: {"description": "Current user information", "model": UserResponse},
        401: {"description": "Not authenticated"},
    },
)
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.

    Args:
        current_user: Authenticated user (injected from JWT)

    Returns:
        UserResponse: Current user information

    Example:
        GET /api/auth/me
        Authorization: Bearer eyJhbGc...

        Response:
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "user@example.com",
            "created_at": "2025-11-05T12:00:00Z",
            "is_active": true
        }
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        created_at=current_user.created_at,
        is_active=current_user.is_active,
    )


@router.post(
    "/refresh",
    response_model=TokenValidationResponse,
    summary="Refresh JWT token",
    description="Refresh JWT token before expiry to extend session.",
    responses={
        200: {"description": "New JWT token created", "model": TokenValidationResponse},
        401: {"description": "Not authenticated"},
    },
)
async def refresh_token(current_user: User = Depends(get_current_user)) -> TokenValidationResponse:
    """
    Refresh JWT token before expiry.

    This endpoint allows users to extend their session by getting a new JWT
    token before the current one expires. The old token remains valid until
    its original expiry time.

    Args:
        current_user: Authenticated user (injected from JWT)

    Returns:
        TokenValidationResponse: New JWT token and user info

    Example:
        POST /api/auth/refresh
        Authorization: Bearer eyJhbGc...

        Response:
        {
            "access_token": "eyJhbGc...",
            "token_type": "bearer",
            "expires_in": 604800,
            "user": {...}
        }
    """
    from app.core.config import get_settings

    # Create new JWT token
    access_token = jwt_service.create_access_token(current_user)
    logger.info(f"JWT refreshed for user {current_user.id}")

    # Calculate expiry in seconds
    settings = get_settings()
    expires_in_seconds = settings.session_expiry_days * 24 * 60 * 60

    return TokenValidationResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
        user=UserResponse(
            id=str(current_user.id),
            email=current_user.email,
            created_at=current_user.created_at,
            is_active=current_user.is_active,
        ),
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout user",
    description=(
        "Logout user by invalidating session. "
        "Note: JWT tokens are stateless, so logout is client-side. "
        "Client must discard the token."
    ),
    responses={
        200: {"description": "Logout successful", "model": LogoutResponse},
        401: {"description": "Not authenticated"},
    },
)
async def logout(current_user: User = Depends(get_current_user)) -> LogoutResponse:
    """
    Logout user (client-side token removal).

    Note: JWT tokens are stateless and cannot be revoked server-side without
    additional infrastructure (token blacklist). This endpoint confirms the
    logout action, but the client must discard the JWT token.

    For true token revocation, implement a token blacklist (future enhancement):
    - Store token JTI (JWT ID) in Redis/database
    - Check blacklist on every request
    - Add token to blacklist on logout

    Args:
        current_user: Authenticated user (injected from JWT)

    Returns:
        LogoutResponse: Logout confirmation message

    Example:
        POST /api/auth/logout
        Authorization: Bearer eyJhbGc...

        Response:
        {
            "message": "Successfully logged out"
        }
    """
    logger.info(f"User {current_user.id} logged out")

    return LogoutResponse(message="Successfully logged out")


def _mask_email(email: str) -> str:
    """
    Mask an email address for security/privacy.

    Examples:
        - "user@example.com" → "u***@example.com"
        - "a@example.com" → "a***@example.com"
        - "verylongemail@example.com" → "v***@example.com"

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


# Future endpoints to be implemented in subsequent stories:
# - POST /auth/validate-token - Validate a 6-digit token
# - POST /auth/refresh - Refresh JWT token
# - POST /auth/logout - Logout and invalidate session
# - GET /auth/me - Get current user information
