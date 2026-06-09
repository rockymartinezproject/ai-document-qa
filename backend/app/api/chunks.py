"""
Chunk retrieval endpoints.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.base import get_db
from app.db.models import Chunk
from app.models.chunk import ChunkOut
from app.models.response import APIResponse

router = APIRouter(prefix="/chunks", tags=["Chunks"])
logger = get_logger("chunks_api")


@router.get("", response_model=APIResponse[list[ChunkOut]])
async def list_chunks(
    request: Request,
    document_id: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    """List all chunks, optionally filtered by document_id."""
    request_id = getattr(request.state, "request_id", None)

    stmt = select(Chunk).order_by(Chunk.document_id, Chunk.index)
    if document_id:
        stmt = stmt.where(Chunk.document_id == document_id)

    result = await session.execute(stmt)
    rows = result.scalars().all()

    return APIResponse(
        success=True,
        data=[ChunkOut.model_validate(r) for r in rows],
        request_id=request_id,
    )
