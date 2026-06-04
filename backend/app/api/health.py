"""
Health check endpoints with dependency diagnostics.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.core.config import settings
from app.core.diagnostics import check_dependencies, get_uptime_seconds
from app.models.response import APIResponse, HealthCheckResponse, ReadinessResponse

router = APIRouter()


@router.get("/health", response_model=APIResponse[HealthCheckResponse], tags=["Health"])
async def health_check(request: Request):
    """Basic health check with metadata."""
    request_id = getattr(request.state, "request_id", None)

    data = HealthCheckResponse(
        status="healthy",
        service="ai-document-qa-api",
        version=settings.PROJECT_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=get_uptime_seconds(),
    )

    return APIResponse(
        success=True,
        data=data,
        request_id=request_id,
    )


@router.get(
    "/health/ready",
    response_model=APIResponse[ReadinessResponse],
    tags=["Health"],
)
async def readiness_check(request: Request):
    """Readiness probe with dependency checks for orchestration."""
    request_id = getattr(request.state, "request_id", None)
    checks = await check_dependencies()

    all_healthy = all(checks.values())

    data = ReadinessResponse(
        status="ready" if all_healthy else "not_ready",
        checks=checks,
    )

    return APIResponse(
        success=all_healthy,
        data=data,
        request_id=request_id,
    )
