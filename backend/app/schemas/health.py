"""
Guardian Health Check Schemas
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """Health check response."""

    status: HealthStatus = Field(
        ...,
        description="Overall health status"
    )

    service: str = Field(
        default="guardian",
        description="Service name"
    )

    version: str = Field(
        ...,
        description="Service version"
    )

    database: Optional[str] = Field(
        default=None,
        description="Database connection status"
    )

    details: Optional[dict] = Field(
        default=None,
        description="Additional health details"
    )
