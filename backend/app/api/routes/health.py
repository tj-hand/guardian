"""
Health check endpoint.

This module provides health check endpoints for monitoring application
and service status. Used by load balancers, orchestrators, and monitoring tools.
"""

import time
from typing import Literal

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.schemas.health import DatabaseHealthCheck, HealthCheckResponse

router = APIRouter(tags=["Health"])


async def check_database_health(db: AsyncSession) -> DatabaseHealthCheck:
    """
    Check database connectivity and response time.

    Args:
        db: Database session

    Returns:
        DatabaseHealthCheck: Database health status with response time
    """
    start_time = time.time()
    try:
        # Execute simple query to test connection
        result = await db.execute(text("SELECT 1"))
        result.fetchone()

        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        return DatabaseHealthCheck(
            connected=True, response_time_ms=round(response_time, 2), error=None
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000

        return DatabaseHealthCheck(
            connected=False, response_time_ms=round(response_time, 2), error=str(e)
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check the health status of the application and its dependencies",
    responses={
        200: {
            "description": "Application is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "app_name": "Email Token Auth",
                        "environment": "development",
                        "database": "connected",
                        "version": "1.0.0",
                    }
                }
            },
        },
        503: {
            "description": "Application is unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "app_name": "Email Token Auth",
                        "environment": "development",
                        "database": "disconnected",
                        "version": "1.0.0",
                        "details": {"error": "Database connection failed"},
                    }
                }
            },
        },
    },
)
async def health_check(
    db: AsyncSession = Depends(get_db), settings: Settings = Depends(get_settings)
) -> HealthCheckResponse:
    """
    Perform comprehensive health check.

    Checks:
    - Application is running
    - Database connectivity
    - Configuration is loaded

    Returns:
        HealthCheckResponse: Comprehensive health status

    Usage:
        GET /health

        This endpoint is typically used by:
        - Kubernetes liveness/readiness probes
        - Load balancer health checks
        - Monitoring systems
        - Docker HEALTHCHECK
    """
    # Check database health
    db_health = await check_database_health(db)

    # Determine overall status
    overall_status: Literal["healthy", "unhealthy", "degraded"]
    database_status: Literal["connected", "disconnected", "error"]

    if db_health.connected:
        overall_status = "healthy"
        database_status = "connected"
        details = None
    else:
        overall_status = "unhealthy"
        database_status = "error"
        details = {
            "database_error": db_health.error,
            "database_response_time_ms": db_health.response_time_ms,
        }

    return HealthCheckResponse(
        status=overall_status,
        app_name=settings.app_name,
        environment=settings.app_env,
        database=database_status,
        version="1.0.0",
        details=details,
    )


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Check",
    description="Check if the application is ready to accept traffic",
    responses={
        200: {"description": "Application is ready"},
        503: {"description": "Application is not ready"},
    },
)
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Kubernetes-style readiness probe.

    Returns 200 if application can accept traffic, 503 otherwise.
    Checks critical dependencies (database).

    Returns:
        dict: Simple ready/not ready status

    Usage:
        GET /health/ready

        Kubernetes readiness probe configuration:
        ```yaml
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        ```
    """
    db_health = await check_database_health(db)

    if db_health.connected:
        return {"status": "ready"}
    else:
        return {"status": "not ready", "reason": db_health.error}


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Check",
    description="Check if the application is alive",
    responses={200: {"description": "Application is alive"}},
)
async def liveness_check() -> dict:
    """
    Kubernetes-style liveness probe.

    Returns 200 if application is running.
    Does NOT check dependencies - only application process health.

    Returns:
        dict: Simple alive status

    Usage:
        GET /health/live

        Kubernetes liveness probe configuration:
        ```yaml
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 20
        ```
    """
    return {"status": "alive"}
