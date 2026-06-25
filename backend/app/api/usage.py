"""
Usage and cost tracking endpoints.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.base import get_db
from app.models.response import APIResponse
from app.models.usage import TotalUsageResponse
from app.services.chat_service import get_total_usage

router = APIRouter(prefix="/usage", tags=["Usage"])
logger = get_logger("usage_api")


@router.get("", response_model=APIResponse[TotalUsageResponse])
async def total_usage(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Return aggregated token usage and cost across all conversations."""
    request_id = getattr(request.state, "request_id", None)

    totals = await get_total_usage(session)

    data = TotalUsageResponse(
        total_input_tokens=totals["input_tokens"],
        total_output_tokens=totals["output_tokens"],
        total_cost=totals["cost"],
    )

    return APIResponse(
        success=True,
        data=data,
        request_id=request_id,
    )
