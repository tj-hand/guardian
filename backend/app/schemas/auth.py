"""
Guardian Authentication Schemas

Pydantic models for request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class TokenRequest(BaseModel):
    """Request body for token generation."""

    email: EmailStr = Field(
        ...,
        description="Email address to send the 6-digit token to",
        examples=["user@example.com"]
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower().strip()


class TokenRequestResponse(BaseModel):
    """Response after requesting a token."""

    message: str = Field(
        default="If the email exists, a 6-digit code has been sent",
        description="Status message"
    )

    email: str = Field(
        ...,
        description="Masked email address",
        examples=["u***@example.com"]
    )

    expires_in_minutes: int = Field(
        ...,
        description="Token expiry time in minutes",
        examples=[10]
    )


class TokenValidation(BaseModel):
    """Request body for token validation."""

    email: EmailStr = Field(
        ...,
        description="Email address used to request the token",
        examples=["user@example.com"]
    )

    token: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit token received via email",
        examples=["123456"]
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower().strip()

    @field_validator("token")
    @classmethod
    def validate_token_format(cls, v: str) -> str:
        """Ensure token is exactly 6 digits."""
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Token must be exactly 6 digits")
        return v


class UserResponse(BaseModel):
    """User information in responses."""

    id: str = Field(
        ...,
        description="User UUID",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    email: str = Field(
        ...,
        description="User email address",
        examples=["user@example.com"]
    )

    created_at: datetime = Field(
        ...,
        description="Account creation timestamp"
    )

    is_active: bool = Field(
        default=True,
        description="Whether user account is active"
    )


class TokenValidationResponse(BaseModel):
    """Response after successful token validation."""

    access_token: str = Field(
        ...,
        description="JWT access token for authentication"
    )

    token_type: str = Field(
        default="bearer",
        description="Token type"
    )

    expires_in: int = Field(
        ...,
        description="Token expiry in seconds",
        examples=[604800]
    )

    user: UserResponse = Field(
        ...,
        description="Authenticated user information"
    )


class LogoutResponse(BaseModel):
    """Response after logout."""

    message: str = Field(
        default="Successfully logged out",
        description="Logout status message"
    )


class RateLimitError(BaseModel):
    """Rate limit exceeded error response."""

    detail: str = Field(
        ...,
        description="Error message",
        examples=["Too many requests. Please try again in 15 minutes."]
    )

    retry_after: int = Field(
        ...,
        description="Seconds until rate limit resets",
        examples=[900]
    )

    attempts_remaining: int = Field(
        default=0,
        description="Remaining attempts in current window"
    )


class RefreshTokenRequest(BaseModel):
    """Optional request for token refresh with additional context."""
    pass


class RefreshTokenResponse(TokenValidationResponse):
    """Response after token refresh (same as validation response)."""
    pass
