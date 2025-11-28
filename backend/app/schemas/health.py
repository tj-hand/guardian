"""
Health check schemas.

This module defines Pydantic models for health check endpoints.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """
    Health check response model.

    Used by the /health endpoint to report application and service status.
    """

    status: Literal["healthy", "unhealthy", "degraded"] = Field(
        description="Overall health status of the application"
    )

    app_name: str = Field(description="Name of the application")

    environment: str = Field(description="Current environment (development, staging, production)")

    database: Literal["connected", "disconnected", "error"] = Field(
        description="Database connection status"
    )

    version: Optional[str] = Field(default="1.0.0", description="Application version")

    details: Optional[dict] = Field(
        default=None, description="Additional health check details (errors, warnings, etc.)"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "status": "healthy",
                "app_name": "Email Token Auth",
                "environment": "development",
                "database": "connected",
                "version": "1.0.0",
                "details": None,
            }
        }


class DatabaseHealthCheck(BaseModel):
    """
    Database-specific health check model.

    Used internally to check database connectivity.
    """

    connected: bool = Field(description="Whether database connection is successful")

    response_time_ms: Optional[float] = Field(
        default=None, description="Database response time in milliseconds"
    )

    error: Optional[str] = Field(default=None, description="Error message if connection failed")
