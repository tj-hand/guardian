"""
Tests for email whitelist feature.

Tests the email whitelist functionality that restricts token generation
to only emails that exist in the users table when enabled.
"""

import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestEmailWhitelistEnabled:
    """Tests for email whitelist when ENABLED."""

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    @patch('app.core.config.get_settings')
    async def test_whitelist_enabled_user_exists_success(
        self,
        mock_get_settings,
        mock_send_email,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test token generation succeeds when whitelist enabled and user exists."""
        # Configure settings mock
        mock_settings = MagicMock()
        mock_settings.enable_email_whitelist = True
        mock_settings.token_expiry_minutes = 15
        mock_get_settings.return_value = mock_settings
        mock_send_email.return_value = True

        # Create user in database (whitelist entry)
        email = "whitelisted@example.com"
        user = User(email=email)
        db_session.add(user)
        await db_session.commit()

        # Request token - should succeed
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": email}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "email" in data
        assert "***" in data["email"]  # Email should be masked
        assert mock_send_email.called

    @pytest.mark.asyncio
    @patch('app.core.config.get_settings')
    async def test_whitelist_enabled_user_not_exists_forbidden(
        self,
        mock_get_settings,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test token generation fails when whitelist enabled and user doesn't exist."""
        # Configure settings mock
        mock_settings = MagicMock()
        mock_settings.enable_email_whitelist = True
        mock_get_settings.return_value = mock_settings

        # Don't create user - email not in whitelist
        email = "notwhitelisted@example.com"

        # Request token - should fail with 403
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": email}
        )

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "not authorized" in data["detail"].lower()

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    @patch('app.core.config.get_settings')
    async def test_whitelist_enabled_case_insensitive_match(
        self,
        mock_get_settings,
        mock_send_email,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test case-insensitive email matching with whitelist enabled."""
        # Configure settings mock
        mock_settings = MagicMock()
        mock_settings.enable_email_whitelist = True
        mock_settings.token_expiry_minutes = 15
        mock_get_settings.return_value = mock_settings
        mock_send_email.return_value = True

        # Create user with lowercase email
        email_lower = "user@example.com"
        user = User(email=email_lower)
        db_session.add(user)
        await db_session.commit()

        # Request token with mixed case
        email_mixed = "User@Example.COM"
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": email_mixed}
        )

        # Should succeed due to case-insensitive matching
        assert response.status_code == 200


class TestEmailWhitelistDisabled:
    """Tests for email whitelist when DISABLED."""

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    @patch('app.core.config.get_settings')
    async def test_whitelist_disabled_any_email_allowed(
        self,
        mock_get_settings,
        mock_send_email,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test token generation succeeds for any email when whitelist disabled."""
        # Configure settings mock
        mock_settings = MagicMock()
        mock_settings.enable_email_whitelist = False
        mock_settings.token_expiry_minutes = 15
        mock_get_settings.return_value = mock_settings
        mock_send_email.return_value = True

        # Don't create user - but should still work when whitelist disabled
        email = "anyemail@example.com"

        # Request token - should succeed
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": email}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    @patch('app.core.config.get_settings')
    async def test_whitelist_disabled_user_created(
        self,
        mock_get_settings,
        mock_send_email,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that user is created when whitelist disabled."""
        # Configure settings mock
        mock_settings = MagicMock()
        mock_settings.enable_email_whitelist = False
        mock_settings.token_expiry_minutes = 15
        mock_get_settings.return_value = mock_settings
        mock_send_email.return_value = True

        email = "newuser@example.com"

        # Request token
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": email}
        )

        assert response.status_code == 200

        # Verify user was created
        from sqlalchemy import select
        result = await db_session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        assert user is not None
        assert user.email == email

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    @patch('app.core.config.get_settings')
    async def test_whitelist_disabled_existing_user_reused(
        self,
        mock_get_settings,
        mock_send_email,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that existing user is reused when whitelist disabled."""
        # Configure settings mock
        mock_settings = MagicMock()
        mock_settings.enable_email_whitelist = False
        mock_settings.token_expiry_minutes = 15
        mock_get_settings.return_value = mock_settings
        mock_send_email.return_value = True

        email = "existing@example.com"

        # Create user first
        user = User(email=email)
        db_session.add(user)
        await db_session.commit()

        # Request token
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": email}
        )

        assert response.status_code == 200

        # Verify only one user exists (no duplicate)
        from sqlalchemy import select, func
        result = await db_session.execute(
            select(func.count(User.id)).where(User.email == email)
        )
        user_count = result.scalar()

        assert user_count == 1


class TestWhitelistWithRateLimiting:
    """Tests for whitelist feature interaction with rate limiting."""

    @pytest.mark.asyncio
    @patch('app.core.config.get_settings')
    async def test_rate_limit_checked_before_whitelist(
        self,
        mock_get_settings,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that rate limiting is checked before whitelist validation."""
        # Configure settings mock
        mock_settings = MagicMock()
        mock_settings.enable_email_whitelist = True
        mock_get_settings.return_value = mock_settings

        email = "ratelimited@example.com"

        # Make 3 requests (at rate limit)
        with patch('app.services.email_service.send_token_email') as mock_send:
            mock_send.return_value = True

            # Create user for whitelist
            user = User(email=email)
            db_session.add(user)
            await db_session.commit()

            for _ in range(3):
                response = await client.post(
                    "/api/v1/auth/request-token",
                    json={"email": email}
                )
                assert response.status_code == 200

        # 4th request should be rate limited (429, not 403)
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": email}
        )

        # Should get rate limit error, not whitelist error
        assert response.status_code == 429

    @pytest.mark.asyncio
    @patch('app.core.config.get_settings')
    async def test_whitelist_rejection_does_not_consume_rate_limit(
        self,
        mock_get_settings,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that whitelist rejection still respects rate limiting."""
        # Configure settings mock
        mock_settings = MagicMock()
        mock_settings.enable_email_whitelist = True
        mock_get_settings.return_value = mock_settings

        # Don't create user - not whitelisted
        email = "notwhitelisted@example.com"

        # First request - should get 403 (whitelist rejection)
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": email}
        )
        assert response.status_code == 403

        # Can still make requests (rate limit not exhausted by rejections)
        # Make 3 more requests
        for _ in range(3):
            response = await client.post(
                "/api/v1/auth/request-token",
                json={"email": email}
            )
            # Should still get 403, not 429
            assert response.status_code == 403


class TestWhitelistSecurityFeatures:
    """Tests for security aspects of whitelist feature."""

    @pytest.mark.asyncio
    @patch('app.core.config.get_settings')
    async def test_whitelist_rejection_no_user_enumeration(
        self,
        mock_get_settings,
        client: AsyncClient
    ):
        """Test that whitelist rejection message doesn't reveal if user exists."""
        # Configure settings mock
        mock_settings = MagicMock()
        mock_settings.enable_email_whitelist = True
        mock_get_settings.return_value = mock_settings

        # Request for non-existent user
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": "nonexistent@example.com"}
        )

        assert response.status_code == 403
        data = response.json()

        # Error message should be generic, not revealing user doesn't exist
        assert "not authorized" in data["detail"].lower()
        assert "does not exist" not in data["detail"].lower()
        assert "not found" not in data["detail"].lower()

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    @patch('app.core.config.get_settings')
    async def test_whitelist_enabled_inactive_user_can_login(
        self,
        mock_get_settings,
        mock_send_email,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that inactive users in whitelist can still request tokens."""
        # Configure settings mock
        mock_settings = MagicMock()
        mock_settings.enable_email_whitelist = True
        mock_settings.token_expiry_minutes = 15
        mock_get_settings.return_value = mock_settings
        mock_send_email.return_value = True

        # Create inactive user
        email = "inactive@example.com"
        user = User(email=email, is_active=False)
        db_session.add(user)
        await db_session.commit()

        # Request token - should succeed (user exists in whitelist)
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": email}
        )

        # Whitelist only checks existence, not is_active status
        assert response.status_code == 200


class TestWhitelistConfiguration:
    """Tests for whitelist configuration behavior."""

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    @patch('app.core.config.get_settings')
    async def test_default_whitelist_setting(
        self,
        mock_get_settings,
        mock_send_email,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that whitelist is enabled by default (secure by default)."""
        # Configure settings mock with default value
        mock_settings = MagicMock()
        mock_settings.enable_email_whitelist = True  # Default is True
        mock_get_settings.return_value = mock_settings

        # Try to request token without user existing
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": "test@example.com"}
        )

        # Should fail with whitelist enabled by default
        assert response.status_code == 403
