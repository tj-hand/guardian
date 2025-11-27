"""
Guardian Authentication Endpoint Tests
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_request_token_success(client: AsyncClient, test_email: str):
    """Test successful token request."""
    response = await client.post(
        "/api/auth/request-token",
        json={"email": test_email}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "email" in data
    assert "expires_in_minutes" in data


@pytest.mark.asyncio
async def test_request_token_invalid_email(client: AsyncClient):
    """Test token request with invalid email."""
    response = await client.post(
        "/api/auth/request-token",
        json={"email": "not-an-email"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_validate_token_invalid(client: AsyncClient, test_email: str):
    """Test token validation with invalid token."""
    response = await client.post(
        "/api/auth/validate-token",
        json={"email": test_email, "token": "000000"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_validate_token_invalid_format(client: AsyncClient, test_email: str):
    """Test token validation with invalid format."""
    response = await client.post(
        "/api/auth/validate-token",
        json={"email": test_email, "token": "12345"}  # Too short
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_me_endpoint_unauthorized(client: AsyncClient):
    """Test /me endpoint without authentication."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_unauthorized(client: AsyncClient):
    """Test token refresh without authentication."""
    response = await client.post("/api/auth/refresh")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_unauthorized(client: AsyncClient):
    """Test logout without authentication."""
    response = await client.post("/api/auth/logout")
    assert response.status_code == 401
