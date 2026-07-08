"""
Embedding status and management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import status as http_status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.logging import get_logger
from app.db.base import get_db
from app.db.models import Chunk, Document, User
from app.models.embedding import EmbedDocumentResponse, EmbeddingStatusResponse
from app.models.response import APIResponse
from app.services.embeddings import get_embedding_provider
from app.services.document_service import embed_chunks_for_document

router = APIRouter(prefix="/embeddings", tags=["Embeddings"])
logger = get_logger("embeddings_api")


@router.get("/status", response_model=APIResponse[EmbeddingStatusResponse])
async def embedding_status(
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current embedding system status for the current user."""
    request_id = getattr(request.state, "request_id", None)
    provider = get_embedding_provider()

    base_stmt = select(Chunk).join(Document).where(Document.user_id == current_user.id)
    total = await session.scalar(
        select(func.count(Chunk.id)).select_from(base_stmt.subquery())
    )
    embedded = await session.scalar(
        select(func.count(Chunk.id)).select_from(
            base_stmt.where(Chunk.embedding.isnot(None)).subquery()
        )
    )

    data = EmbeddingStatusResponse(
        provider=provider.name,
        dimension=provider.dimension,
        total_chunks=total or 0,
        embedded_chunks=embedded or 0,
        pending_chunks=(total or 0) - (embedded or 0),
    )

    return APIResponse(
        success=True,
        data=data,
        request_id=request_id,
    )


@router.post("/embed/{document_id}", response_model=APIResponse[EmbedDocumentResponse])
async def embed_document(
    request: Request,
    document_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate embeddings for all chunks of a specific document."""
    request_id = getattr(request.state, "request_id", None)

    doc_result = await session.execute(
        select(Document).where(
            Document.id == document_id, Document.user_id == current_user.id
        )
    )
    if doc_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    count = await embed_chunks_for_document(session, document_id)
    if count == 0:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Document not found or has no chunks to embed.",
        )

    provider = get_embedding_provider()

    data = EmbedDocumentResponse(
        document_id=document_id,
        chunks_processed=count,
        provider=provider.name,
        message=f"Embedded {count} chunks using {provider.name}.",
    )

    return APIResponse(
        success=True,
        data=data,
        request_id=request_id,
    )
