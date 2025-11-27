"""
Guardian Health Endpoint Tests
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns API info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Guardian"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "guardian"
    assert "status" in data


@pytest.mark.asyncio
async def test_liveness_probe(client: AsyncClient):
    """Test liveness probe."""
    response = await client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness_probe(client: AsyncClient):
    """Test readiness probe."""
    response = await client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
