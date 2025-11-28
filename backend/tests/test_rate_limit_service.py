"""
Unit tests for rate limit service.

Tests rate limiting functionality for token requests.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import rate_limit_service, token_service
from app.models.user import User
from app.models.token import Token
from app.core.config import get_settings


settings = get_settings()


class TestCheckRateLimit:
    """Tests for rate limit checking by user ID."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_first_request(
        self,
        db_session: AsyncSession
    ):
        """Test rate limit check for user's first request."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Check rate limit (first request)
        allowed, remaining, retry_after = await rate_limit_service.check_rate_limit(
            db_session,
            str(user.id)
        )

        # Should be allowed
        assert allowed is True
        assert remaining == settings.rate_limit_requests
        assert retry_after == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_within_limit(
        self,
        db_session: AsyncSession
    ):
        """Test rate limit check when within allowed requests."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create some tokens (less than limit)
        num_requests = settings.rate_limit_requests - 1
        for i in range(num_requests):
            await token_service.create_token_for_user(
                db_session,
                str(user.id),
                f"12345{i}"
            )

        # Check rate limit
        allowed, remaining, retry_after = await rate_limit_service.check_rate_limit(
            db_session,
            str(user.id)
        )

        # Should be allowed
        assert allowed is True
        assert remaining == 1
        assert retry_after == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_at_limit(
        self,
        db_session: AsyncSession
    ):
        """Test rate limit check when at the exact limit."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create tokens up to limit
        for i in range(settings.rate_limit_requests):
            await token_service.create_token_for_user(
                db_session,
                str(user.id),
                f"12345{i}"
            )

        # Check rate limit
        allowed, remaining, retry_after = await rate_limit_service.check_rate_limit(
            db_session,
            str(user.id)
        )

        # Should NOT be allowed
        assert allowed is False
        assert remaining == 0
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(
        self,
        db_session: AsyncSession
    ):
        """Test rate limit check when limit is exceeded."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create tokens exceeding limit
        for i in range(settings.rate_limit_requests + 2):
            await token_service.create_token_for_user(
                db_session,
                str(user.id),
                f"12345{i}"
            )

        # Check rate limit
        allowed, remaining, retry_after = await rate_limit_service.check_rate_limit(
            db_session,
            str(user.id)
        )

        # Should NOT be allowed
        assert allowed is False
        assert remaining == 0
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_retry_after_calculation(
        self,
        db_session: AsyncSession
    ):
        """Test that retry_after is calculated correctly."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create tokens at limit
        for i in range(settings.rate_limit_requests):
            await token_service.create_token_for_user(
                db_session,
                str(user.id),
                f"12345{i}"
            )

        # Check rate limit
        allowed, remaining, retry_after = await rate_limit_service.check_rate_limit(
            db_session,
            str(user.id)
        )

        # Verify retry_after is reasonable
        assert retry_after > 0
        assert retry_after <= settings.rate_limit_window_minutes * 60

    @pytest.mark.asyncio
    async def test_check_rate_limit_window_expiry(
        self,
        db_session: AsyncSession
    ):
        """Test rate limit resets after window expires."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create old tokens outside window
        window_start = datetime.now(timezone.utc) - timedelta(
            minutes=settings.rate_limit_window_minutes + 5
        )
        for i in range(settings.rate_limit_requests):
            token_hash = token_service.hash_token(f"12345{i}")
            db_token = Token(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
                created_at=window_start
            )
            db_session.add(db_token)

        await db_session.commit()

        # Check rate limit (old tokens should not count)
        allowed, remaining, retry_after = await rate_limit_service.check_rate_limit(
            db_session,
            str(user.id)
        )

        # Should be allowed (window reset)
        assert allowed is True
        assert remaining == settings.rate_limit_requests
        assert retry_after == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_partial_window(
        self,
        db_session: AsyncSession
    ):
        """Test rate limit with tokens both inside and outside window."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create old tokens (outside window)
        old_time = datetime.now(timezone.utc) - timedelta(
            minutes=settings.rate_limit_window_minutes + 1
        )
        for i in range(2):
            token_hash = token_service.hash_token(f"old{i}")
            db_token = Token(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
                created_at=old_time
            )
            db_session.add(db_token)

        # Create recent tokens (inside window)
        for i in range(2):
            await token_service.create_token_for_user(
                db_session,
                str(user.id),
                f"new{i}"
            )

        # Check rate limit
        allowed, remaining, retry_after = await rate_limit_service.check_rate_limit(
            db_session,
            str(user.id)
        )

        # Should only count recent tokens
        assert allowed is True
        assert remaining == settings.rate_limit_requests - 2
        assert retry_after == 0

    @pytest.mark.asyncio
    @patch('app.services.rate_limit_service.logger')
    async def test_check_rate_limit_logs_warning_when_exceeded(
        self,
        mock_logger: MagicMock,
        db_session: AsyncSession
    ):
        """Test that rate limit logs warning when exceeded."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create tokens exceeding limit
        for i in range(settings.rate_limit_requests):
            await token_service.create_token_for_user(
                db_session,
                str(user.id),
                f"12345{i}"
            )

        # Check rate limit
        await rate_limit_service.check_rate_limit(db_session, str(user.id))

        # Verify warning logged
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args
        assert "Rate limit exceeded" in warning_call[0][0]

    @pytest.mark.asyncio
    @patch('app.services.rate_limit_service.logger')
    async def test_check_rate_limit_logs_info_when_allowed(
        self,
        mock_logger: MagicMock,
        db_session: AsyncSession
    ):
        """Test that rate limit logs info when request is allowed."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Check rate limit
        await rate_limit_service.check_rate_limit(db_session, str(user.id))

        # Verify info logged
        mock_logger.info.assert_called_once()
        info_call = mock_logger.info.call_args
        assert "Rate limit check passed" in info_call[0][0]


class TestCheckRateLimitByEmail:
    """Tests for rate limit checking by email address."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_by_email_new_user(
        self,
        db_session: AsyncSession
    ):
        """Test rate limit check for new user (doesn't exist yet)."""
        email = "newuser@example.com"

        # Check rate limit for non-existent user
        allowed, remaining, retry_after = await rate_limit_service.check_rate_limit_by_email(
            db_session,
            email
        )

        # Should be allowed (first time)
        assert allowed is True
        assert remaining == settings.rate_limit_requests - 1
        assert retry_after == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_by_email_existing_user(
        self,
        db_session: AsyncSession
    ):
        """Test rate limit check for existing user."""
        # Create test user with tokens
        user = User(email="existing@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create some tokens
        for i in range(2):
            await token_service.create_token_for_user(
                db_session,
                str(user.id),
                f"12345{i}"
            )

        # Check rate limit by email
        allowed, remaining, retry_after = await rate_limit_service.check_rate_limit_by_email(
            db_session,
            "existing@example.com"
        )

        # Should be allowed with correct remaining count
        assert allowed is True
        assert remaining == settings.rate_limit_requests - 2
        assert retry_after == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_by_email_at_limit(
        self,
        db_session: AsyncSession
    ):
        """Test rate limit by email when user is at limit."""
        # Create test user with tokens at limit
        user = User(email="limited@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create tokens up to limit
        for i in range(settings.rate_limit_requests):
            await token_service.create_token_for_user(
                db_session,
                str(user.id),
                f"12345{i}"
            )

        # Check rate limit by email
        allowed, remaining, retry_after = await rate_limit_service.check_rate_limit_by_email(
            db_session,
            "limited@example.com"
        )

        # Should NOT be allowed
        assert allowed is False
        assert remaining == 0
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_by_email_case_sensitivity(
        self,
        db_session: AsyncSession
    ):
        """Test rate limit by email handles case sensitivity correctly."""
        # Create user with lowercase email
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create tokens
        for i in range(2):
            await token_service.create_token_for_user(
                db_session,
                str(user.id),
                f"12345{i}"
            )

        # Check with exact email
        allowed, remaining, _ = await rate_limit_service.check_rate_limit_by_email(
            db_session,
            "test@example.com"
        )

        # Should find user and count tokens
        assert allowed is True
        assert remaining == settings.rate_limit_requests - 2


class TestGetRateLimitInfo:
    """Tests for rate limit information retrieval."""

    @pytest.mark.asyncio
    async def test_get_rate_limit_info_no_requests(
        self,
        db_session: AsyncSession
    ):
        """Test getting rate limit info for user with no requests."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Get rate limit info
        info = await rate_limit_service.get_rate_limit_info(
            db_session,
            str(user.id)
        )

        # Verify info structure
        assert info["limit"] == settings.rate_limit_requests
        assert info["window_minutes"] == settings.rate_limit_window_minutes
        assert info["current_count"] == 0
        assert "window_start" in info
        assert info["is_limited"] is False

    @pytest.mark.asyncio
    async def test_get_rate_limit_info_with_requests(
        self,
        db_session: AsyncSession
    ):
        """Test getting rate limit info for user with requests."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create some tokens
        num_tokens = 2
        for i in range(num_tokens):
            await token_service.create_token_for_user(
                db_session,
                str(user.id),
                f"12345{i}"
            )

        # Get rate limit info
        info = await rate_limit_service.get_rate_limit_info(
            db_session,
            str(user.id)
        )

        # Verify current count
        assert info["current_count"] == num_tokens
        assert info["is_limited"] is False

    @pytest.mark.asyncio
    async def test_get_rate_limit_info_at_limit(
        self,
        db_session: AsyncSession
    ):
        """Test getting rate limit info when user is at limit."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create tokens up to limit
        for i in range(settings.rate_limit_requests):
            await token_service.create_token_for_user(
                db_session,
                str(user.id),
                f"12345{i}"
            )

        # Get rate limit info
        info = await rate_limit_service.get_rate_limit_info(
            db_session,
            str(user.id)
        )

        # Should show limited
        assert info["current_count"] == settings.rate_limit_requests
        assert info["is_limited"] is True

    @pytest.mark.asyncio
    async def test_get_rate_limit_info_window_start_format(
        self,
        db_session: AsyncSession
    ):
        """Test that window_start is properly formatted as ISO string."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Get rate limit info
        info = await rate_limit_service.get_rate_limit_info(
            db_session,
            str(user.id)
        )

        # Verify window_start is ISO format string
        window_start = info["window_start"]
        assert isinstance(window_start, str)
        # Should be parseable as datetime
        datetime.fromisoformat(window_start)

    @pytest.mark.asyncio
    async def test_get_rate_limit_info_only_counts_window(
        self,
        db_session: AsyncSession
    ):
        """Test that rate limit info only counts tokens within window."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create old tokens (outside window)
        old_time = datetime.now(timezone.utc) - timedelta(
            minutes=settings.rate_limit_window_minutes + 1
        )
        for i in range(3):
            token_hash = token_service.hash_token(f"old{i}")
            db_token = Token(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
                created_at=old_time
            )
            db_session.add(db_token)

        # Create recent tokens (inside window)
        for i in range(2):
            await token_service.create_token_for_user(
                db_session,
                str(user.id),
                f"new{i}"
            )

        # Get rate limit info
        info = await rate_limit_service.get_rate_limit_info(
            db_session,
            str(user.id)
        )

        # Should only count recent tokens
        assert info["current_count"] == 2


class TestRateLimitEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_rate_limit_with_zero_tokens(
        self,
        db_session: AsyncSession
    ):
        """Test rate limit check with user who has no tokens."""
        # Create test user (no tokens)
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Check rate limit
        allowed, remaining, retry_after = await rate_limit_service.check_rate_limit(
            db_session,
            str(user.id)
        )

        # Should be allowed with full quota
        assert allowed is True
        assert remaining == settings.rate_limit_requests
        assert retry_after == 0

    @pytest.mark.asyncio
    async def test_rate_limit_concurrent_requests_simulation(
        self,
        db_session: AsyncSession
    ):
        """Test rate limit with rapid successive checks."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Simulate rapid requests
        results = []
        for i in range(settings.rate_limit_requests + 1):
            # Create token
            await token_service.create_token_for_user(
                db_session,
                str(user.id),
                f"token{i}"
            )
            # Check rate limit
            allowed, remaining, retry_after = await rate_limit_service.check_rate_limit(
                db_session,
                str(user.id)
            )
            results.append((allowed, remaining, retry_after))

        # Last request should be denied
        last_allowed, last_remaining, last_retry = results[-1]
        assert last_allowed is False
        assert last_remaining == 0
        assert last_retry > 0

    @pytest.mark.asyncio
    async def test_rate_limit_minimum_retry_after(
        self,
        db_session: AsyncSession
    ):
        """Test that retry_after is at least 1 second."""
        # Create test user
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create tokens at limit
        for i in range(settings.rate_limit_requests):
            await token_service.create_token_for_user(
                db_session,
                str(user.id),
                f"12345{i}"
            )

        # Check rate limit
        allowed, remaining, retry_after = await rate_limit_service.check_rate_limit(
            db_session,
            str(user.id)
        )

        # Verify retry_after is at least 1
        assert retry_after >= 1
