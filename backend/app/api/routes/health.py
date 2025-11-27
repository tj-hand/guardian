"""
Guardian Health Check Routes

Endpoints for monitoring and container orchestration.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.health import HealthResponse, HealthStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Full health check",
    description="Check overall service health including database connectivity."
)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Full health check with database connectivity test.
    """
    db_status = "unknown"
    overall_status = HealthStatus.HEALTHY

    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
        overall_status = HealthStatus.UNHEALTHY

    return HealthResponse(
        status=overall_status,
        service="guardian",
        version=settings.app_version,
        database=db_status,
        details={
            "environment": settings.environment,
            "debug": settings.debug,
        }
    )


@router.get(
    "/health/live",
    summary="Liveness probe",
    description="Simple liveness check for Kubernetes/Docker."
)
async def liveness() -> dict:
    """
    Liveness probe - just confirm the service is running.
    """
    return {"status": "alive"}


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description="Check if service is ready to accept requests."
)
async def readiness(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Readiness probe - check database connectivity.
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "reason": "database_unavailable"}
