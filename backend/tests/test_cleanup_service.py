"""
Unit tests for cleanup service.

Tests background cleanup functionality for expired tokens.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import Token
from app.models.user import User
from app.services import cleanup_service, token_service


class TestCleanupExpiredTokens:
    """Tests for expired token cleanup functionality."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_success(self, db_session: AsyncSession):
        """Test successful cleanup of expired tokens."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create expired tokens
        for i in range(5):
            token_hash = token_service.hash_token(f"12345{i}")
            expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
            created_at = expires_at - timedelta(minutes=15)  # Created before expiry
            db_token = Token(
                user_id=user.id, token_hash=token_hash, expires_at=expires_at, created_at=created_at
            )
            db_session.add(db_token)

        # Create valid token
        await token_service.create_token_for_user(db_session, str(user.id), "999999")

        await db_session.commit()

        # Execute cleanup
        deleted_count = await cleanup_service.cleanup_expired_tokens(db_session)

        # Verify cleanup
        assert deleted_count == 5

        # Verify valid token still exists
        valid_token = await token_service.validate_token_for_user(
            db_session, str(user.id), "999999"
        )
        assert valid_token is not None

    @pytest.mark.asyncio
    async def test_cleanup_no_expired_tokens(self, db_session: AsyncSession):
        """Test cleanup when there are no expired tokens."""
        # Create test user with only valid tokens
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create valid tokens
        for i in range(3):
            await token_service.create_token_for_user(db_session, str(user.id), f"12345{i}")

        # Execute cleanup
        deleted_count = await cleanup_service.cleanup_expired_tokens(db_session)

        # No tokens should be deleted
        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_cleanup_preserves_used_but_valid_tokens(self, db_session: AsyncSession):
        """Test cleanup preserves used tokens that haven't expired yet."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create used token that's not expired
        token = await token_service.create_token_for_user(db_session, str(user.id), "123456")
        await token_service.mark_token_as_used(db_session, token)

        # Create expired token
        expired_token_hash = token_service.hash_token("999999")
        expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        created_at = expires_at - timedelta(minutes=15)  # Created before expiry
        expired_token = Token(
            user_id=user.id,
            token_hash=expired_token_hash,
            expires_at=expires_at,
            created_at=created_at,
        )
        db_session.add(expired_token)
        await db_session.commit()

        # Execute cleanup
        deleted_count = await cleanup_service.cleanup_expired_tokens(db_session)

        # Only expired token should be deleted
        assert deleted_count == 1

    @pytest.mark.asyncio
    async def test_cleanup_multiple_users(self, db_session: AsyncSession):
        """Test cleanup works correctly across multiple users."""
        # Create multiple users with expired tokens
        for i in range(3):
            user = User(email=f"user{i}@example.com")
            db_session.add(user)
            await db_session.commit()
            await db_session.refresh(user)

            # Create expired tokens for each user
            for j in range(2):
                token_hash = token_service.hash_token(f"token{i}{j}")
                expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
                created_at = expires_at - timedelta(minutes=15)  # Created before expiry
                db_token = Token(
                    user_id=user.id,
                    token_hash=token_hash,
                    expires_at=expires_at,
                    created_at=created_at,
                )
                db_session.add(db_token)

        await db_session.commit()

        # Execute cleanup
        deleted_count = await cleanup_service.cleanup_expired_tokens(db_session)

        # Should delete all expired tokens (3 users * 2 tokens = 6)
        assert deleted_count == 6

    @pytest.mark.asyncio
    async def test_cleanup_edge_case_just_expired(self, db_session: AsyncSession):
        """Test cleanup handles tokens that just expired."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create token that expires exactly now (or very recently)
        token_hash = token_service.hash_token("123456")
        expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        created_at = expires_at - timedelta(minutes=15)  # Created before expiry
        db_token = Token(
            user_id=user.id, token_hash=token_hash, expires_at=expires_at, created_at=created_at
        )
        db_session.add(db_token)
        await db_session.commit()

        # Execute cleanup
        deleted_count = await cleanup_service.cleanup_expired_tokens(db_session)

        # Token should be deleted
        assert deleted_count == 1

    @pytest.mark.asyncio
    async def test_cleanup_empty_database(self, db_session: AsyncSession):
        """Test cleanup with empty database."""
        # Execute cleanup on empty database
        deleted_count = await cleanup_service.cleanup_expired_tokens(db_session)

        # No tokens to delete
        assert deleted_count == 0

    @pytest.mark.asyncio
    @patch("app.services.cleanup_service.logger")
    async def test_cleanup_logs_success(self, mock_logger: MagicMock, db_session: AsyncSession):
        """Test that cleanup logs success message."""
        # Create test user with expired token
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token_hash = token_service.hash_token("123456")
        expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        created_at = expires_at - timedelta(minutes=15)  # Created before expiry
        db_token = Token(
            user_id=user.id, token_hash=token_hash, expires_at=expires_at, created_at=created_at
        )
        db_session.add(db_token)
        await db_session.commit()

        # Execute cleanup
        await cleanup_service.cleanup_expired_tokens(db_session)

        # Verify logging
        assert mock_logger.info.call_count >= 2
        mock_logger.info.assert_any_call("Starting expired token cleanup")

    @pytest.mark.asyncio
    @patch("app.services.cleanup_service.logger")
    @patch("app.services.token_service.cleanup_expired_tokens")
    async def test_cleanup_logs_error_on_exception(
        self, mock_cleanup: AsyncMock, mock_logger: MagicMock, db_session: AsyncSession
    ):
        """Test that cleanup logs error when exception occurs."""
        # Mock cleanup to raise exception
        mock_cleanup.side_effect = Exception("Database error")

        # Execute cleanup and expect exception
        with pytest.raises(Exception, match="Database error"):
            await cleanup_service.cleanup_expired_tokens(db_session)

        # Verify error logging
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args
        assert "Error during token cleanup" in error_call[0][0]

    @pytest.mark.asyncio
    async def test_cleanup_returns_correct_count(self, db_session: AsyncSession):
        """Test that cleanup returns accurate count of deleted tokens."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create specific number of expired tokens
        num_expired = 7
        for i in range(num_expired):
            token_hash = token_service.hash_token(f"token{i}")
            expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
            created_at = expires_at - timedelta(minutes=15)  # Created before expiry
            db_token = Token(
                user_id=user.id, token_hash=token_hash, expires_at=expires_at, created_at=created_at
            )
            db_session.add(db_token)

        await db_session.commit()

        # Execute cleanup
        deleted_count = await cleanup_service.cleanup_expired_tokens(db_session)

        # Verify exact count
        assert deleted_count == num_expired

    @pytest.mark.asyncio
    async def test_cleanup_idempotent(self, db_session: AsyncSession):
        """Test that running cleanup multiple times is safe."""
        # Create test user with expired token
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token_hash = token_service.hash_token("123456")
        expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        created_at = expires_at - timedelta(minutes=15)  # Created before expiry
        db_token = Token(
            user_id=user.id, token_hash=token_hash, expires_at=expires_at, created_at=created_at
        )
        db_session.add(db_token)
        await db_session.commit()

        # First cleanup
        deleted_count_1 = await cleanup_service.cleanup_expired_tokens(db_session)
        assert deleted_count_1 == 1

        # Second cleanup (should find nothing)
        deleted_count_2 = await cleanup_service.cleanup_expired_tokens(db_session)
        assert deleted_count_2 == 0

        # Third cleanup (should still find nothing)
        deleted_count_3 = await cleanup_service.cleanup_expired_tokens(db_session)
        assert deleted_count_3 == 0


class TestCleanupIntegration:
    """Integration tests for cleanup service with real token operations."""

    @pytest.mark.asyncio
    async def test_cleanup_after_token_validation(self, db_session: AsyncSession):
        """Test cleanup works after normal token validation flow."""
        # Create user and generate token
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = "123456"
        db_token = await token_service.create_token_for_user(db_session, str(user.id), token)

        # Validate and mark as used
        validated_token = await token_service.validate_token_for_user(
            db_session, str(user.id), token
        )
        await token_service.mark_token_as_used(db_session, validated_token)

        # Manually expire the token for testing
        # Set created_at first to satisfy the check constraint (expires_at > created_at)
        db_token.created_at = datetime.now(timezone.utc) - timedelta(minutes=20)
        db_token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await db_session.commit()

        # Cleanup should remove expired token
        deleted_count = await cleanup_service.cleanup_expired_tokens(db_session)
        assert deleted_count == 1

    @pytest.mark.asyncio
    async def test_cleanup_with_rate_limit_tokens(self, db_session: AsyncSession):
        """Test cleanup works with tokens created during rate limiting."""
        # Create user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create multiple tokens (simulating rate limit scenario)
        for i in range(5):
            token_hash = token_service.hash_token(f"token{i}")
            # Some expired, some valid
            expiry_offset = -10 if i < 3 else 10
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_offset)
            # For expired tokens, set created_at before expires_at
            # For valid tokens, created_at can be recent
            created_at = expires_at - timedelta(minutes=15)
            db_token = Token(
                user_id=user.id, token_hash=token_hash, expires_at=expires_at, created_at=created_at
            )
            db_session.add(db_token)

        await db_session.commit()

        # Cleanup should only remove expired ones
        deleted_count = await cleanup_service.cleanup_expired_tokens(db_session)
        assert deleted_count == 3
