"""
Integration tests for authentication routes.

Tests the /api/auth endpoints with full request/response cycle.
"""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services import token_service


class TestRequestTokenEndpoint:
    """Tests for POST /api/v1/auth/request-token endpoint."""

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    async def test_request_token_success(
        self,
        mock_send_email,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test successful token request."""
        # Mock email sending
        mock_send_email.return_value = True

        # Request token
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": "user@example.com"}
        )

        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "email" in data
        assert "expires_in_minutes" in data
        assert "***" in data["email"]  # Email should be masked
        assert data["expires_in_minutes"] == 15

        # Verify email was sent
        assert mock_send_email.called

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    async def test_request_token_creates_user(
        self,
        mock_send_email,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that requesting token creates user if doesn't exist."""
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
    async def test_request_token_stores_token(
        self,
        mock_send_email,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that token is stored in database."""
        mock_send_email.return_value = True

        email = "user@example.com"

        # Request token
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": email}
        )

        assert response.status_code == 200

        # Verify user exists
        from sqlalchemy import select
        result = await db_session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        assert user is not None

        # Verify token was stored
        from app.models.token import Token
        result = await db_session.execute(
            select(Token).where(Token.user_id == user.id)
        )
        tokens = result.scalars().all()

        assert len(tokens) == 1
        assert tokens[0].user_id == user.id
        assert tokens[0].used_at is None

    @pytest.mark.asyncio
    async def test_request_token_invalid_email(self, client: AsyncClient):
        """Test token request with invalid email format."""
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": "not-an-email"}
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_request_token_missing_email(self, client: AsyncClient):
        """Test token request without email field."""
        response = await client.post(
            "/api/v1/auth/request-token",
            json={}
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    async def test_request_token_existing_user(
        self,
        mock_send_email,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test token request for existing user."""
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


class TestRateLimiting:
    """Tests for rate limiting on token requests."""

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    async def test_rate_limit_enforcement(
        self,
        mock_send_email,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that rate limiting is enforced after 3 requests."""
        mock_send_email.return_value = True

        email = "ratelimit@example.com"

        # Make 3 successful requests
        for _ in range(3):
            response = await client.post(
                "/api/v1/auth/request-token",
                json={"email": email}
            )
            assert response.status_code == 200

        # 4th request should be rate limited
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": email}
        )

        assert response.status_code == 429  # Too Many Requests

        data = response.json()
        assert "detail" in data
        assert "retry_after" in data

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    async def test_rate_limit_per_email(
        self,
        mock_send_email,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that rate limiting is per email address."""
        mock_send_email.return_value = True

        email1 = "user1@example.com"
        email2 = "user2@example.com"

        # Make 3 requests for email1
        for _ in range(3):
            response = await client.post(
                "/api/v1/auth/request-token",
                json={"email": email1}
            )
            assert response.status_code == 200

        # email1 should be rate limited
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": email1}
        )
        assert response.status_code == 429

        # But email2 should still work
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": email2}
        )
        assert response.status_code == 200


class TestSecurityFeatures:
    """Tests for security features in auth endpoints."""

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    async def test_email_masking_in_response(
        self,
        mock_send_email,
        client: AsyncClient
    ):
        """Test that email is masked in response."""
        mock_send_email.return_value = True

        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": "user@example.com"}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["email"] == "u***@example.com"

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    async def test_consistent_response_for_nonexistent_email(
        self,
        mock_send_email,
        client: AsyncClient
    ):
        """Test that response is same for nonexistent email (security)."""
        mock_send_email.return_value = True

        # Request token for nonexistent email
        response1 = await client.post(
            "/api/v1/auth/request-token",
            json={"email": "nonexistent@example.com"}
        )

        # Request token for another nonexistent email
        response2 = await client.post(
            "/api/v1/auth/request-token",
            json={"email": "another@example.com"}
        )

        # Both should return 200
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Messages should be the same
        assert response1.json()["message"] == response2.json()["message"]

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    async def test_no_error_details_on_email_failure(
        self,
        mock_send_email,
        client: AsyncClient
    ):
        """Test that email sending errors don't expose details."""
        # Mock email service to raise exception
        mock_send_email.side_effect = Exception("Email service down")

        # Request should still return 200 (security)
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": "user@example.com"}
        )

        # Should still return success to avoid revealing email send failure
        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch('app.services.email_service.send_token_email')
    async def test_token_is_hashed_in_database(
        self,
        mock_send_email,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that tokens are hashed (not stored in plaintext)."""
        mock_send_email.return_value = True

        email = "user@example.com"

        # Request token
        response = await client.post(
            "/api/v1/auth/request-token",
            json={"email": email}
        )

        assert response.status_code == 200

        # Get token from database
        from sqlalchemy import select
        from app.models.user import User
        from app.models.token import Token

        result = await db_session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one()

        result = await db_session.execute(
            select(Token).where(Token.user_id == user.id)
        )
        token = result.scalar_one()

        # Token hash should be 64 characters (SHA-256)
        assert len(token.token_hash) == 64
        assert token.token_hash.isalnum()


class TestErrorHandling:
    """Tests for error handling in auth endpoints."""

    @pytest.mark.asyncio
    async def test_malformed_json(self, client: AsyncClient):
        """Test handling of malformed JSON."""
        response = await client.post(
            "/api/v1/auth/request-token",
            content="not json",
            headers={"Content-Type": "application/json"}
        )

        # Should return validation error
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_empty_request_body(self, client: AsyncClient):
        """Test handling of empty request body."""
        response = await client.post(
            "/api/v1/auth/request-token",
            json=None
        )

        # Should return validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_extra_fields_ignored(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that extra fields in request are ignored."""
        with patch('app.services.email_service.send_token_email') as mock:
            mock.return_value = True

            response = await client.post(
                "/api/v1/auth/request-token",
                json={
                    "email": "user@example.com",
                    "extra_field": "should be ignored"
                }
            )

            # Should still succeed
            assert response.status_code == 200
