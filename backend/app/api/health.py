"""
Health check endpoints.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "ai-document-qa-api"}


@router.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness probe for orchestration."""
    return {"status": "ready"}
