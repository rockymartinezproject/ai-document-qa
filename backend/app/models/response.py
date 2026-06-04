"""
Standardized API response models.
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard envelope for all API responses."""

    success: bool = Field(default=True, description="Whether the request succeeded")
    data: Optional[T] = Field(default=None, description="Response payload")
    message: Optional[str] = Field(default=None, description="Human-readable message")
    request_id: Optional[str] = Field(default=None, description="Request correlation ID")


class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: str
    service: str
    version: str
    environment: str
    timestamp: str
    uptime_seconds: float
    dependencies: Optional[dict] = None


class ReadinessResponse(BaseModel):
    """Readiness probe response model."""

    status: str
    checks: dict
