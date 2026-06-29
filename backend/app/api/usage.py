"""
Usage and cost tracking endpoints.
"""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.base import get_db
from app.models.response import APIResponse
from app.models.usage import TotalUsageResponse, UsageBreakdownResponse
from app.services.chat_service import get_total_usage, get_usage_breakdown

router = APIRouter(prefix="/usage", tags=["Usage"])
logger = get_logger("usage_api")

GroupBy = Literal["day", "model", "conversation"]


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


@router.get("/breakdown", response_model=APIResponse[UsageBreakdownResponse])
async def usage_breakdown(
    request: Request,
    group_by: GroupBy = Query(..., description="Dimension to group usage by"),
    days: Optional[int] = Query(default=None, ge=1, description="Limit to the last N days"),
    session: AsyncSession = Depends(get_db),
):
    """Return usage/cost aggregated by day, model, or conversation."""
    request_id = getattr(request.state, "request_id", None)

    try:
        items = await get_usage_breakdown(session, group_by=group_by, days=days)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    data = UsageBreakdownResponse(
        group_by=group_by,
        days=days,
        items=[
            {
                "label": item["label"],
                "input_tokens": item["input_tokens"],
                "output_tokens": item["output_tokens"],
                "cost": item["cost"],
                "count": item["count"],
            }
            for item in items
        ],
    )

    return APIResponse(
        success=True,
        data=data,
        request_id=request_id,
    )
