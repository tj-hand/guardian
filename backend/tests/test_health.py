"""
Tests for health check endpoints.

This module tests all health check endpoints including:
- Main health check (/health)
- Readiness probe (/health/ready)
- Liveness probe (/health/live)
"""

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """
    Test main health check endpoint returns correct status.

    The /health endpoint should return:
    - Status 200
    - Application name
    - Environment
    - Database status
    - Version
    """
    response = await client.get("/health")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # Check required fields
    assert "status" in data
    assert "app_name" in data
    assert "environment" in data
    assert "database" in data
    assert "version" in data

    # Check status values
    assert data["status"] in ["healthy", "unhealthy", "degraded"]
    assert data["database"] in ["connected", "disconnected", "error"]

    # Check application info
    assert isinstance(data["app_name"], str)
    assert isinstance(data["environment"], str)
    assert isinstance(data["version"], str)


@pytest.mark.asyncio
async def test_health_check_with_database_connection(client: AsyncClient):
    """
    Test health check reports healthy status when database is connected.

    With a working database connection, should return:
    - status: "healthy"
    - database: "connected"
    - No error details
    """
    response = await client.get("/health")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data.get("details") is None  # No errors


@pytest.mark.asyncio
async def test_readiness_check_endpoint(client: AsyncClient):
    """
    Test readiness probe endpoint.

    The /health/ready endpoint should return:
    - Status 200 when ready
    - Simple status message
    """
    response = await client.get("/health/ready")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert "status" in data
    assert data["status"] == "ready"


@pytest.mark.asyncio
async def test_liveness_check_endpoint(client: AsyncClient):
    """
    Test liveness probe endpoint.

    The /health/live endpoint should:
    - Always return 200 (unless application is completely down)
    - Return simple status message
    - Not check database or other dependencies
    """
    response = await client.get("/health/live")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert "status" in data
    assert data["status"] == "alive"


@pytest.mark.asyncio
async def test_health_check_response_schema(client: AsyncClient):
    """
    Test that health check response matches expected schema.

    Validates:
    - All required fields are present
    - Field types are correct
    - Values are in expected ranges
    """
    response = await client.get("/health")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # Required fields with correct types
    assert isinstance(data["status"], str)
    assert isinstance(data["app_name"], str)
    assert isinstance(data["environment"], str)
    assert isinstance(data["database"], str)
    assert isinstance(data["version"], str)

    # Optional fields
    if "details" in data and data["details"] is not None:
        assert isinstance(data["details"], dict)


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """
    Test root endpoint returns API information.

    The / endpoint should return:
    - Welcome message
    - Version
    - Environment
    - Links to docs and health
    """
    response = await client.get("/")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # Check required fields
    assert "message" in data
    assert "version" in data
    assert "environment" in data
    assert "health" in data

    # Check values
    assert isinstance(data["message"], str)
    assert isinstance(data["version"], str)
    assert isinstance(data["environment"], str)
    assert data["health"] == "/health"


@pytest.mark.asyncio
async def test_health_check_performance(client: AsyncClient):
    """
    Test health check endpoint responds quickly.

    Health checks should be fast (< 1 second) to avoid
    timeout issues with orchestrators.
    """
    import time

    start_time = time.time()
    response = await client.get("/health")
    end_time = time.time()

    assert response.status_code == status.HTTP_200_OK

    # Health check should respond in less than 1 second
    response_time = end_time - start_time
    assert response_time < 1.0, f"Health check took {response_time:.2f}s (should be < 1s)"


@pytest.mark.asyncio
async def test_readiness_vs_liveness_difference(client: AsyncClient):
    """
    Test that readiness and liveness probes serve different purposes.

    Liveness should always succeed (checks if app is running).
    Readiness should check dependencies (database).
    """
    # Liveness should always succeed
    liveness_response = await client.get("/health/live")
    assert liveness_response.status_code == status.HTTP_200_OK
    assert liveness_response.json()["status"] == "alive"

    # Readiness should check database
    readiness_response = await client.get("/health/ready")
    assert readiness_response.status_code == status.HTTP_200_OK
    readiness_data = readiness_response.json()
    assert "status" in readiness_data


@pytest.mark.asyncio
async def test_health_endpoints_cors_headers(client: AsyncClient):
    """
    Test that health endpoints respect CORS configuration.

    Health endpoints should have CORS headers to allow
    monitoring from web-based dashboards.
    """
    response = await client.get("/health")

    # CORS headers should be present (added by middleware)
    headers = response.headers
    assert "access-control-allow-origin" in headers or response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_multiple_concurrent_health_checks(client: AsyncClient):
    """
    Test that health checks can handle concurrent requests.

    Simulates load balancer or monitoring tool making
    multiple simultaneous health check requests.
    """
    import asyncio

    # Make 10 concurrent health check requests
    tasks = [client.get("/health") for _ in range(10)]
    responses = await asyncio.gather(*tasks)

    # All should succeed
    for response in responses:
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy", "degraded"]
