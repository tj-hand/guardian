"""
Tests for FastAPI dependencies.

This module tests:
- get_current_user - with various scenarios
- get_current_active_user - inactive user handling
- get_optional_current_user - optional authentication
"""

import pytest
from httpx import AsyncClient

from app.models.user import User
from app.services import jwt_service


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_inactive_user(
        self, async_client: AsyncClient, db_session
    ):
        """Test that inactive user is rejected."""
        # Arrange - Create inactive user
        user = User(email="inactive@example.com", is_active=False)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create token for inactive user
        token = jwt_service.create_access_token(user)
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await async_client.get("/api/v1/auth/me", headers=headers)

        # Assert - User should be rejected as inactive
        assert response.status_code == 401
        assert "inactive" in response.json()["detail"].lower()


class TestGetCurrentActiveUser:
    """Tests for get_current_active_user dependency."""

    @pytest.mark.asyncio
    async def test_active_user_passes(
        self, async_client: AsyncClient, sample_user, auth_headers
    ):
        """Test that active user is allowed through."""
        # Act
        response = await async_client.get("/api/v1/auth/me", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["email"] == sample_user.email


class TestGetOptionalCurrentUser:
    """Tests for get_optional_current_user dependency.

    Note: These tests are indirect since get_optional_current_user
    isn't currently exposed via any endpoint. We test the underlying
    logic via unit tests.
    """

    @pytest.mark.asyncio
    async def test_optional_auth_without_token(self, db_session):
        """Test get_optional_current_user returns None without token."""
        from app.api.dependencies import get_optional_current_user

        # Act - Call without credentials
        result = await get_optional_current_user(credentials=None, db=db_session)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_optional_auth_with_valid_token(self, db_session, sample_user):
        """Test get_optional_current_user returns user with valid token."""
        from unittest.mock import MagicMock

        from app.api.dependencies import get_optional_current_user

        # Arrange - Create mock credentials with valid token
        token = jwt_service.create_access_token(sample_user)
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        # Act
        result = await get_optional_current_user(
            credentials=mock_credentials, db=db_session
        )

        # Assert
        assert result is not None
        assert result.id == sample_user.id
        assert result.email == sample_user.email

    @pytest.mark.asyncio
    async def test_optional_auth_with_invalid_token(self, db_session):
        """Test get_optional_current_user returns None with invalid token."""
        from unittest.mock import MagicMock

        from app.api.dependencies import get_optional_current_user

        # Arrange - Create mock credentials with invalid token
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid.token.here"

        # Act
        result = await get_optional_current_user(
            credentials=mock_credentials, db=db_session
        )

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_optional_auth_with_expired_token(self, db_session, sample_user):
        """Test get_optional_current_user returns None with expired token."""
        from datetime import timedelta
        from unittest.mock import MagicMock

        from app.api.dependencies import get_optional_current_user

        # Arrange - Create mock credentials with expired token
        expired_token = jwt_service.create_access_token(
            sample_user, timedelta(hours=-1)
        )
        mock_credentials = MagicMock()
        mock_credentials.credentials = expired_token

        # Act
        result = await get_optional_current_user(
            credentials=mock_credentials, db=db_session
        )

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_optional_auth_with_inactive_user(self, db_session):
        """Test get_optional_current_user returns None for inactive user."""
        from unittest.mock import MagicMock

        from app.api.dependencies import get_optional_current_user

        # Arrange - Create inactive user
        user = User(email="inactive2@example.com", is_active=False)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create token for inactive user
        token = jwt_service.create_access_token(user)
        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        # Act
        result = await get_optional_current_user(
            credentials=mock_credentials, db=db_session
        )

        # Assert - Inactive user returns None for optional auth
        assert result is None

    @pytest.mark.asyncio
    async def test_optional_auth_with_deleted_user(self, db_session, sample_user):
        """Test get_optional_current_user returns None for deleted user."""
        from unittest.mock import MagicMock

        from app.api.dependencies import get_optional_current_user

        # Arrange - Create token then delete user
        token = jwt_service.create_access_token(sample_user)

        # Delete the user
        await db_session.delete(sample_user)
        await db_session.commit()

        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        # Act
        result = await get_optional_current_user(
            credentials=mock_credentials, db=db_session
        )

        # Assert - Deleted user returns None
        assert result is None
