"""
Tests for JWT service (token creation, validation, decoding).

This module tests JWT token lifecycle:
- Token creation with user data
- Token decoding and validation
- Token verification
- Expiry handling
- Custom expiration times
"""

import asyncio
import pytest
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

from app.services import jwt_service
from app.models.user import User
from app.core.config import get_settings


settings = get_settings()


class TestCreateAccessToken:
    """Tests for JWT access token creation."""

    @pytest.mark.asyncio
    async def test_create_access_token_default_expiry(self, sample_user):
        """Test creating JWT token with default 7-day expiry."""
        # Act
        token = jwt_service.create_access_token(sample_user)

        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify payload
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        assert payload["sub"] == str(sample_user.id)
        assert payload["email"] == sample_user.email
        assert "exp" in payload
        assert "iat" in payload

    @pytest.mark.asyncio
    async def test_create_access_token_custom_expiry(self, sample_user):
        """Test creating JWT token with custom expiration time."""
        # Arrange
        custom_expiry = timedelta(hours=1)

        # Act
        token = jwt_service.create_access_token(sample_user, custom_expiry)

        # Assert
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])

        # Verify expiry is approximately 1 hour from now
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        expected_exp = now + custom_expiry

        # Allow 5 second tolerance for test execution time
        assert abs((exp_datetime - expected_exp).total_seconds()) < 5

    @pytest.mark.asyncio
    async def test_create_access_token_contains_required_claims(self, sample_user):
        """Test that JWT token contains all required claims."""
        # Act
        token = jwt_service.create_access_token(sample_user)
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])

        # Assert
        assert "sub" in payload  # Subject (user ID)
        assert "email" in payload  # Custom claim
        assert "exp" in payload  # Expiration
        assert "iat" in payload  # Issued at

        assert payload["sub"] == str(sample_user.id)
        assert payload["email"] == sample_user.email

    @pytest.mark.asyncio
    async def test_create_access_token_expiry_calculation(self, sample_user):
        """Test that token expiry is calculated correctly."""
        # Act
        token = jwt_service.create_access_token(sample_user)
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])

        # Assert
        exp_timestamp = payload["exp"]
        iat_timestamp = payload["iat"]

        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        iat_datetime = datetime.fromtimestamp(iat_timestamp, tz=timezone.utc)

        # Default expiry should be 7 days
        expected_delta = timedelta(days=settings.session_expiry_days)
        actual_delta = exp_datetime - iat_datetime

        # Allow 5 second tolerance
        assert abs((actual_delta - expected_delta).total_seconds()) < 5


class TestDecodeAccessToken:
    """Tests for JWT token decoding."""

    @pytest.mark.asyncio
    async def test_decode_valid_token(self, sample_user):
        """Test decoding a valid JWT token."""
        # Arrange
        token = jwt_service.create_access_token(sample_user)

        # Act
        payload = jwt_service.decode_access_token(token)

        # Assert
        assert payload["sub"] == str(sample_user.id)
        assert payload["email"] == sample_user.email

    @pytest.mark.asyncio
    async def test_decode_expired_token(self, sample_user):
        """Test that decoding expired token raises JWTError."""
        # Arrange - Create token that expires in -1 hour (already expired)
        token = jwt_service.create_access_token(
            sample_user,
            timedelta(hours=-1)
        )

        # Act & Assert
        with pytest.raises(JWTError):
            jwt_service.decode_access_token(token)

    @pytest.mark.asyncio
    async def test_decode_invalid_signature(self, sample_user):
        """Test that invalid signature raises JWTError."""
        # Arrange
        token = jwt_service.create_access_token(sample_user)

        # Tamper with token by changing last character
        tampered_token = token[:-1] + ("X" if token[-1] != "X" else "Y")

        # Act & Assert
        with pytest.raises(JWTError):
            jwt_service.decode_access_token(tampered_token)

    def test_decode_malformed_token(self):
        """Test that malformed token raises JWTError."""
        # Arrange
        malformed_token = "not.a.valid.jwt.token"

        # Act & Assert
        with pytest.raises(JWTError):
            jwt_service.decode_access_token(malformed_token)

    def test_decode_empty_token(self):
        """Test that empty token raises JWTError."""
        # Act & Assert
        with pytest.raises(JWTError):
            jwt_service.decode_access_token("")


class TestVerifyToken:
    """Tests for JWT token verification (convenience wrapper)."""

    @pytest.mark.asyncio
    async def test_verify_valid_token(self, sample_user):
        """Test verifying a valid token returns user ID."""
        # Arrange
        token = jwt_service.create_access_token(sample_user)

        # Act
        user_id = jwt_service.verify_token(token)

        # Assert
        assert user_id == str(sample_user.id)

    @pytest.mark.asyncio
    async def test_verify_expired_token(self, sample_user):
        """Test verifying expired token returns None."""
        # Arrange
        token = jwt_service.create_access_token(
            sample_user,
            timedelta(hours=-1)
        )

        # Act
        user_id = jwt_service.verify_token(token)

        # Assert
        assert user_id is None

    def test_verify_invalid_token(self):
        """Test verifying invalid token returns None."""
        # Act
        user_id = jwt_service.verify_token("invalid.token.here")

        # Assert
        assert user_id is None

    @pytest.mark.asyncio
    async def test_verify_token_missing_sub_claim(self, sample_user):
        """Test token without 'sub' claim returns None."""
        # Arrange - Manually create token without 'sub' claim
        payload = {
            "email": sample_user.email,
            "exp": datetime.now(timezone.utc) + timedelta(days=1)
        }
        token = jwt.encode(payload, settings.secret_key, algorithm="HS256")

        # Act
        user_id = jwt_service.verify_token(token)

        # Assert
        assert user_id is None

    def test_verify_empty_token(self):
        """Test verifying empty token returns None."""
        # Act
        user_id = jwt_service.verify_token("")

        # Assert
        assert user_id is None


class TestGetTokenExpirySeconds:
    """Tests for token expiry helper function."""

    def test_get_token_expiry_seconds(self):
        """Test getting token expiry in seconds."""
        # Act
        expiry_seconds = jwt_service.get_token_expiry_seconds()

        # Assert
        expected_seconds = settings.session_expiry_days * 24 * 60 * 60
        assert expiry_seconds == expected_seconds

    def test_get_token_expiry_default_7_days(self):
        """Test default expiry is 7 days (604800 seconds)."""
        # Act
        expiry_seconds = jwt_service.get_token_expiry_seconds()

        # Assert
        # Default is 7 days = 604800 seconds
        assert expiry_seconds == 7 * 24 * 60 * 60
        assert expiry_seconds == 604800


class TestTokenLifecycle:
    """Integration tests for complete token lifecycle."""

    @pytest.mark.asyncio
    async def test_complete_token_lifecycle(self, sample_user):
        """Test creating, decoding, and verifying a token."""
        # Step 1: Create token
        token = jwt_service.create_access_token(sample_user)
        assert token is not None

        # Step 2: Decode token
        payload = jwt_service.decode_access_token(token)
        assert payload["sub"] == str(sample_user.id)
        assert payload["email"] == sample_user.email

        # Step 3: Verify token
        user_id = jwt_service.verify_token(token)
        assert user_id == str(sample_user.id)

    @pytest.mark.asyncio
    async def test_token_becomes_invalid_after_expiry(self, sample_user):
        """Test that token becomes invalid after expiration."""
        # Arrange - Create token that expires in 1 second
        token = jwt_service.create_access_token(
            sample_user,
            timedelta(seconds=1)
        )

        # Act - Token should be valid immediately
        user_id = jwt_service.verify_token(token)
        assert user_id == str(sample_user.id)

        # Wait for expiry using async sleep (non-blocking)
        await asyncio.sleep(2)

        # Assert - Token should now be invalid
        user_id = jwt_service.verify_token(token)
        assert user_id is None

    @pytest.mark.asyncio
    async def test_multiple_tokens_for_same_user(self, sample_user):
        """Test creating multiple tokens for same user."""
        # Act
        token1 = jwt_service.create_access_token(sample_user)
        token2 = jwt_service.create_access_token(sample_user)

        # Assert - Both tokens should be valid but different
        assert token1 != token2

        user_id1 = jwt_service.verify_token(token1)
        user_id2 = jwt_service.verify_token(token2)

        assert user_id1 == str(sample_user.id)
        assert user_id2 == str(sample_user.id)
