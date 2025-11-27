"""
Authentication Schemas

Pydantic models for authentication endpoints (token generation, validation, session management).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator


# ========================================
# Token Request & Response
# ========================================

class TokenRequest(BaseModel):
    """Request model for requesting a 6-digit token via email."""

    email: EmailStr = Field(
        ...,
        description="User's email address",
        example="user@example.com"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class TokenRequestResponse(BaseModel):
    """Response after requesting a token."""

    message: str = Field(
        ...,
        description="Success message",
        example="If the email exists, a 6-digit code has been sent"
    )
    email: str = Field(
        ...,
        description="Email address (masked for security)",
        example="u***@example.com"
    )
    expires_in_minutes: int = Field(
        ...,
        description="Token expiry time in minutes",
        example=15
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "If the email exists, a 6-digit code has been sent",
                "email": "u***@example.com",
                "expires_in_minutes": 15
            }
        }


# ========================================
# Token Validation
# ========================================

class TokenValidation(BaseModel):
    """Request model for validating a 6-digit token."""

    email: EmailStr = Field(
        ...,
        description="User's email address",
        example="user@example.com"
    )
    token: str = Field(
        ...,
        description="6-digit numeric token",
        min_length=6,
        max_length=6,
        example="123456"
    )

    @validator('token')
    def validate_token_format(cls, v):
        """Ensure token is exactly 6 digits."""
        if not v.isdigit():
            raise ValueError('Token must contain only digits')
        if len(v) != 6:
            raise ValueError('Token must be exactly 6 digits')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "token": "123456"
            }
        }


class TokenValidationResponse(BaseModel):
    """Response after successful token validation."""

    access_token: str = Field(
        ...,
        description="JWT access token",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
        example="bearer"
    )
    expires_in: int = Field(
        ...,
        description="Token expiry time in seconds",
        example=604800
    )
    user: "UserResponse" = Field(
        ...,
        description="User information"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 604800,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "created_at": "2025-11-05T12:00:00Z",
                    "is_active": True
                }
            }
        }


# ========================================
# User Information
# ========================================

class UserResponse(BaseModel):
    """User information returned in responses."""

    id: str = Field(
        ...,
        description="User UUID",
        example="123e4567-e89b-12d3-a456-426614174000"
    )
    email: str = Field(
        ...,
        description="User's email address",
        example="user@example.com"
    )
    created_at: datetime = Field(
        ...,
        description="User creation timestamp",
        example="2025-11-05T12:00:00Z"
    )
    is_active: bool = Field(
        ...,
        description="Whether user account is active",
        example=True
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "created_at": "2025-11-05T12:00:00Z",
                "is_active": True
            }
        }


# ========================================
# Session Management
# ========================================

class RefreshTokenRequest(BaseModel):
    """Request model for refreshing JWT token."""

    refresh_token: Optional[str] = Field(
        None,
        description="Refresh token (optional, can use current JWT)",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class LogoutResponse(BaseModel):
    """Response after logout."""

    message: str = Field(
        default="Successfully logged out",
        description="Logout confirmation message",
        example="Successfully logged out"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Successfully logged out"
            }
        }


# ========================================
# Error Responses
# ========================================

class AuthErrorResponse(BaseModel):
    """Error response for authentication failures."""

    detail: str = Field(
        ...,
        description="Error detail message",
        example="Invalid or expired token"
    )
    error_code: Optional[str] = Field(
        None,
        description="Machine-readable error code",
        example="TOKEN_EXPIRED"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid or expired token",
                "error_code": "TOKEN_EXPIRED"
            }
        }


class RateLimitError(BaseModel):
    """Rate limit error response."""

    detail: str = Field(
        ...,
        description="Rate limit error message",
        example="Too many requests. Please try again in 10 minutes."
    )
    retry_after: int = Field(
        ...,
        description="Seconds until retry is allowed",
        example=600
    )
    attempts_remaining: int = Field(
        default=0,
        description="Number of attempts remaining",
        example=0
    )

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Too many requests. Please try again in 10 minutes.",
                "retry_after": 600,
                "attempts_remaining": 0
            }
        }


# Update forward references
TokenValidationResponse.model_rebuild()
