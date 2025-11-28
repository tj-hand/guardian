"""
Unit tests for token service.

Tests token generation, hashing, storage, validation, and cleanup.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import token_service
from app.models.user import User
from app.models.token import Token


class TestTokenGeneration:
    """Tests for token generation functions."""

    def test_generate_6_digit_token_format(self):
        """Test that generated token is exactly 6 digits."""
        token = token_service.generate_6_digit_token()

        assert len(token) == 6
        assert token.isdigit()
        assert 0 <= int(token) <= 999999

    def test_generate_6_digit_token_zero_padding(self):
        """Test that tokens are zero-padded correctly."""
        # Generate multiple tokens and check they're all 6 digits
        tokens = [token_service.generate_6_digit_token() for _ in range(100)]

        for token in tokens:
            assert len(token) == 6
            assert token.isdigit()

    def test_generate_6_digit_token_randomness(self):
        """Test that tokens are random (not always the same)."""
        tokens = [token_service.generate_6_digit_token() for _ in range(50)]

        # Should have some variation (not all identical)
        unique_tokens = set(tokens)
        assert len(unique_tokens) > 1

    def test_hash_token(self):
        """Test token hashing produces consistent SHA-256 hash."""
        token = "123456"
        hash1 = token_service.hash_token(token)
        hash2 = token_service.hash_token(token)

        # Same token should produce same hash
        assert hash1 == hash2

        # Hash should be 64 characters (SHA-256 hex)
        assert len(hash1) == 64
        assert all(c in '0123456789abcdef' for c in hash1)

    def test_hash_token_different_inputs(self):
        """Test that different tokens produce different hashes."""
        hash1 = token_service.hash_token("123456")
        hash2 = token_service.hash_token("654321")

        assert hash1 != hash2


class TestTokenStorage:
    """Tests for token storage and retrieval."""

    @pytest.mark.asyncio
    async def test_create_token_for_user(self, db_session: AsyncSession):
        """Test creating and storing a token for a user."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create token
        token = "123456"
        db_token = await token_service.create_token_for_user(
            db_session,
            str(user.id),
            token
        )

        assert db_token.id is not None
        assert db_token.user_id == user.id
        assert db_token.token_hash == token_service.hash_token(token)
        assert db_token.expires_at > datetime.now(timezone.utc)
        assert db_token.used_at is None

    @pytest.mark.asyncio
    async def test_create_token_expiry_time(self, db_session: AsyncSession):
        """Test that token has correct expiry time."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create token
        before_creation = datetime.now(timezone.utc)
        db_token = await token_service.create_token_for_user(
            db_session,
            str(user.id),
            "123456"
        )
        after_creation = datetime.now(timezone.utc)

        # Token should expire approximately 15 minutes from now
        from app.core.config import get_settings
        settings = get_settings()

        expected_expiry_min = before_creation + timedelta(
            minutes=settings.token_expiry_minutes
        )
        expected_expiry_max = after_creation + timedelta(
            minutes=settings.token_expiry_minutes
        )

        assert expected_expiry_min <= db_token.expires_at <= expected_expiry_max


class TestTokenValidation:
    """Tests for token validation."""

    @pytest.mark.asyncio
    async def test_validate_valid_token(self, db_session: AsyncSession):
        """Test validating a valid, unused token."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create token
        token = "123456"
        await token_service.create_token_for_user(
            db_session,
            str(user.id),
            token
        )

        # Validate token
        validated_token = await token_service.validate_token_for_user(
            db_session,
            str(user.id),
            token
        )

        assert validated_token is not None
        assert validated_token.user_id == user.id
        assert validated_token.is_valid()

    @pytest.mark.asyncio
    async def test_validate_invalid_token(self, db_session: AsyncSession):
        """Test validating a token that doesn't exist."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Try to validate non-existent token
        validated_token = await token_service.validate_token_for_user(
            db_session,
            str(user.id),
            "999999"
        )

        assert validated_token is None

    @pytest.mark.asyncio
    async def test_validate_used_token(self, db_session: AsyncSession):
        """Test that used tokens cannot be validated."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create and use token
        token = "123456"
        db_token = await token_service.create_token_for_user(
            db_session,
            str(user.id),
            token
        )

        # Mark as used
        await token_service.mark_token_as_used(db_session, db_token)

        # Try to validate used token
        validated_token = await token_service.validate_token_for_user(
            db_session,
            str(user.id),
            token
        )

        assert validated_token is None

    @pytest.mark.asyncio
    async def test_validate_expired_token(self, db_session: AsyncSession):
        """Test that expired tokens cannot be validated."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create token with past expiry
        token_hash = token_service.hash_token("123456")
        expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        created_at = expires_at - timedelta(minutes=15)  # Created before expiry
        db_token = Token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=created_at
        )
        db_session.add(db_token)
        await db_session.commit()

        # Try to validate expired token
        validated_token = await token_service.validate_token_for_user(
            db_session,
            str(user.id),
            "123456"
        )

        assert validated_token is None


class TestTokenManagement:
    """Tests for token management functions."""

    @pytest.mark.asyncio
    async def test_mark_token_as_used(self, db_session: AsyncSession):
        """Test marking a token as used."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create token
        token = "123456"
        db_token = await token_service.create_token_for_user(
            db_session,
            str(user.id),
            token
        )

        assert db_token.used_at is None

        # Mark as used
        await token_service.mark_token_as_used(db_session, db_token)

        assert db_token.used_at is not None
        assert not db_token.is_valid()

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(self, db_session: AsyncSession):
        """Test cleanup of expired tokens."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create expired tokens
        for i in range(3):
            token_hash = token_service.hash_token(f"12345{i}")
            expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
            created_at = expires_at - timedelta(minutes=15)  # Created before expiry
            db_token = Token(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                created_at=created_at
            )
            db_session.add(db_token)

        # Create valid token
        await token_service.create_token_for_user(
            db_session,
            str(user.id),
            "999999"
        )

        await db_session.commit()

        # Cleanup expired tokens
        deleted_count = await token_service.cleanup_expired_tokens(db_session)

        assert deleted_count == 3

        # Verify valid token still exists
        valid_token = await token_service.validate_token_for_user(
            db_session,
            str(user.id),
            "999999"
        )
        assert valid_token is not None


class TestUserManagement:
    """Tests for user management functions."""

    @pytest.mark.asyncio
    async def test_get_or_create_user_by_email_new_user(
        self,
        db_session: AsyncSession
    ):
        """Test creating a new user."""
        email = "newuser@example.com"

        user = await token_service.get_or_create_user_by_email(
            db_session,
            email
        )

        assert user.id is not None
        assert user.email == email
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_get_or_create_user_by_email_existing_user(
        self,
        db_session: AsyncSession
    ):
        """Test getting an existing user."""
        email = "existing@example.com"

        # Create user first
        user1 = await token_service.get_or_create_user_by_email(
            db_session,
            email
        )

        # Get same user again
        user2 = await token_service.get_or_create_user_by_email(
            db_session,
            email
        )

        assert user1.id == user2.id
        assert user1.email == user2.email
