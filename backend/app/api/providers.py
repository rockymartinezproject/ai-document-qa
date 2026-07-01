"""
LLM provider discovery endpoint.
"""

from typing import List

from fastapi import APIRouter, Request

from app.core.logging import get_logger
from app.models.response import APIResponse

logger = get_logger("providers_api")

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.get("", response_model=APIResponse[List[dict]])
async def list_providers(request: Request):
    """Return supported LLM providers and their availability."""
    from app.services.llm import list_available_providers

    request_id = getattr(request.state, "request_id", None)
    providers = list_available_providers()

    return APIResponse(
        success=True,
        data=providers,
        request_id=request_id,
    )
