"""
Tests for authentication validation endpoints.

This module tests:
- POST /auth/validate-token - Token validation and JWT creation
- GET /auth/me - Current user information
- POST /auth/refresh - JWT token refresh
- POST /auth/logout - User logout
"""

import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient

from app.services import token_service, jwt_service
from app.models.user import User


class TestValidateTokenEndpoint:
    """Tests for POST /auth/validate-token endpoint."""

    @pytest.mark.asyncio
    async def test_validate_token_success(
        self,
        async_client: AsyncClient,
        db_session,
        sample_user
    ):
        """Test successful token validation and JWT creation."""
        # Arrange - Generate and store token
        token = token_service.generate_6_digit_token()
        await token_service.create_token_for_user(
            db_session,
            str(sample_user.id),
            token
        )

        # Act
        response = await async_client.post(
            "/api/v1/auth/validate-token",
            json={
                "email": sample_user.email,
                "token": token
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data

        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 7 * 24 * 60 * 60  # 7 days in seconds

        # Verify user data
        user_data = data["user"]
        assert user_data["id"] == str(sample_user.id)
        assert user_data["email"] == sample_user.email
        assert user_data["is_active"] is True

        # Verify JWT is valid
        user_id = jwt_service.verify_token(data["access_token"])
        assert user_id == str(sample_user.id)

    @pytest.mark.asyncio
    async def test_validate_token_invalid_email(
        self,
        async_client: AsyncClient,
        db_session
    ):
        """Test token validation with non-existent email."""
        # Act
        response = await async_client.post(
            "/api/v1/auth/validate-token",
            json={
                "email": "nonexistent@example.com",
                "token": "123456"
            }
        )

        # Assert
        assert response.status_code == 401
        assert "Invalid email or token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_validate_token_invalid_token(
        self,
        async_client: AsyncClient,
        db_session,
        sample_user
    ):
        """Test token validation with wrong token."""
        # Arrange - Create correct token
        correct_token = token_service.generate_6_digit_token()
        await token_service.create_token_for_user(
            db_session,
            str(sample_user.id),
            correct_token
        )

        # Act - Try with wrong token
        response = await async_client.post(
            "/api/v1/auth/validate-token",
            json={
                "email": sample_user.email,
                "token": "000000"  # Wrong token
            }
        )

        # Assert
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_validate_token_expired_token(
        self,
        async_client: AsyncClient,
        db_session,
        sample_user
    ):
        """Test token validation with expired token."""
        # Arrange - Create token that's already expired
        token = token_service.generate_6_digit_token()
        token_hash = token_service.hash_token(token)

        from app.models.token import Token

        expired_token_obj = Token(
            user_id=str(sample_user.id),
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)
        )
        db_session.add(expired_token_obj)
        await db_session.commit()

        # Act
        response = await async_client.post(
            "/api/v1/auth/validate-token",
            json={
                "email": sample_user.email,
                "token": token
            }
        )

        # Assert
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_validate_token_already_used(
        self,
        async_client: AsyncClient,
        db_session,
        sample_user
    ):
        """Test that token can only be used once."""
        # Arrange - Generate and store token
        token = token_service.generate_6_digit_token()
        await token_service.create_token_for_user(
            db_session,
            str(sample_user.id),
            token
        )

        # Act - First validation (should succeed)
        response1 = await async_client.post(
            "/api/v1/auth/validate-token",
            json={
                "email": sample_user.email,
                "token": token
            }
        )

        # Assert first validation succeeded
        assert response1.status_code == 200

        # Act - Second validation (should fail - token already used)
        response2 = await async_client.post(
            "/api/v1/auth/validate-token",
            json={
                "email": sample_user.email,
                "token": token
            }
        )

        # Assert second validation failed
        assert response2.status_code == 401
        assert "Invalid or expired token" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_validate_token_invalid_format(
        self,
        async_client: AsyncClient
    ):
        """Test validation with invalid token format."""
        # Act
        response = await async_client.post(
            "/api/v1/auth/validate-token",
            json={
                "email": "user@example.com",
                "token": "abc123"  # Not all digits
            }
        )

        # Assert - Should fail validation
        assert response.status_code == 422


class TestMeEndpoint:
    """Tests for GET /auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self,
        async_client: AsyncClient,
        sample_user,
        auth_headers
    ):
        """Test getting current user information with valid JWT."""
        # Act
        response = await async_client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(sample_user.id)
        assert data["email"] == sample_user.email
        assert data["is_active"] is True
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(
        self,
        async_client: AsyncClient
    ):
        """Test /me endpoint without authentication."""
        # Act
        response = await async_client.get("/api/v1/auth/me")

        # Assert
        assert response.status_code == 403  # Forbidden (no auth header)

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self,
        async_client: AsyncClient
    ):
        """Test /me endpoint with invalid JWT."""
        # Act
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(
        self,
        async_client: AsyncClient,
        sample_user
    ):
        """Test /me endpoint with expired JWT."""
        # Arrange - Create expired token
        expired_token = jwt_service.create_access_token(
            sample_user,
            timedelta(hours=-1)
        )

        # Act
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        # Assert
        assert response.status_code == 401


class TestRefreshEndpoint:
    """Tests for POST /auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self,
        async_client: AsyncClient,
        sample_user,
        auth_headers
    ):
        """Test refreshing JWT token successfully."""
        # Act
        response = await async_client.post(
            "/api/v1/auth/refresh",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data

        assert data["token_type"] == "bearer"

        # Verify new JWT is valid
        user_id = jwt_service.verify_token(data["access_token"])
        assert user_id == str(sample_user.id)

        # Verify user data
        assert data["user"]["id"] == str(sample_user.id)
        assert data["user"]["email"] == sample_user.email

    @pytest.mark.asyncio
    async def test_refresh_token_no_auth(
        self,
        async_client: AsyncClient
    ):
        """Test refresh endpoint without authentication."""
        # Act
        response = await async_client.post("/api/v1/auth/refresh")

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_token(
        self,
        async_client: AsyncClient
    ):
        """Test refresh endpoint with invalid JWT."""
        # Act
        response = await async_client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": "Bearer invalid.token"}
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_generates_new_token(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """Test that refresh generates a new token (not same as old)."""
        # Arrange
        old_token = auth_headers["Authorization"].replace("Bearer ", "")

        # Act
        response = await async_client.post(
            "/api/v1/auth/refresh",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        new_token = response.json()["access_token"]

        # Tokens should be different (different iat timestamp)
        assert new_token != old_token


class TestLogoutEndpoint:
    """Tests for POST /auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """Test successful logout."""
        # Act
        response = await async_client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert data["message"] == "Successfully logged out"

    @pytest.mark.asyncio
    async def test_logout_no_auth(
        self,
        async_client: AsyncClient
    ):
        """Test logout without authentication."""
        # Act
        response = await async_client.post("/api/v1/auth/logout")

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_logout_invalid_token(
        self,
        async_client: AsyncClient
    ):
        """Test logout with invalid JWT."""
        # Act
        response = await async_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer invalid.token"}
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_token_still_valid_after(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """
        Test that JWT remains valid after logout.

        Note: This is expected behavior since JWTs are stateless.
        True revocation requires token blacklist (future enhancement).
        """
        # Act - Logout
        response = await async_client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Act - Try to use token after logout
        response = await async_client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )

        # Assert - Token still works (stateless JWT behavior)
        assert response.status_code == 200


class TestAuthenticationFlow:
    """Integration tests for complete authentication flows."""

    @pytest.mark.asyncio
    async def test_complete_auth_flow(
        self,
        async_client: AsyncClient,
        db_session,
        sample_user
    ):
        """Test complete authentication flow from token to logout."""
        # Step 1: Validate token and get JWT
        token = token_service.generate_6_digit_token()
        await token_service.create_token_for_user(
            db_session,
            str(sample_user.id),
            token
        )

        validate_response = await async_client.post(
            "/api/v1/auth/validate-token",
            json={
                "email": sample_user.email,
                "token": token
            }
        )
        assert validate_response.status_code == 200
        jwt_token = validate_response.json()["access_token"]

        auth_headers = {"Authorization": f"Bearer {jwt_token}"}

        # Step 2: Access protected route (/me)
        me_response = await async_client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == sample_user.email

        # Step 3: Refresh token
        refresh_response = await async_client.post(
            "/api/v1/auth/refresh",
            headers=auth_headers
        )
        assert refresh_response.status_code == 200
        new_jwt_token = refresh_response.json()["access_token"]

        # Step 4: Use new token to access protected route
        new_auth_headers = {"Authorization": f"Bearer {new_jwt_token}"}
        me_response2 = await async_client.get(
            "/api/v1/auth/me",
            headers=new_auth_headers
        )
        assert me_response2.status_code == 200

        # Step 5: Logout
        logout_response = await async_client.post(
            "/api/v1/auth/logout",
            headers=new_auth_headers
        )
        assert logout_response.status_code == 200
