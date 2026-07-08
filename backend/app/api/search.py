"""
Vector/keyword/hybrid search and Qdrant sync endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.logging import get_logger
from app.db.base import get_db
from app.db.models import Chunk, Document, User
from app.models.response import APIResponse
from app.models.search import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SyncDocumentResponse,
    VectorStoreStatusResponse,
)
from app.services.embeddings import deserialize_embedding, get_embedding_provider
from app.services.hybrid_search import hybrid_search
from app.services.keyword_search import search_chunks_keywords
from app.services.vector_store import (
    count_points,
    delete_document_chunks,
    get_qdrant_client,
    search_similar,
    upsert_chunk_points,
)

router = APIRouter(prefix="/search", tags=["Search"])
logger = get_logger("search_api")


@router.get("/status", response_model=APIResponse[VectorStoreStatusResponse])
async def vector_store_status(request: Request):
    """Check Qdrant vector store health and stats."""
    request_id = getattr(request.state, "request_id", None)

    try:
        client = get_qdrant_client()
        await client.get_collections()
        total = await count_points()
        is_healthy = True
    except Exception as e:
        logger.error("Qdrant health check failed: %s", e)
        total = 0
        is_healthy = False

    from app.core.config import settings

    data = VectorStoreStatusResponse(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        qdrant_host=settings.QDRANT_HOST,
        qdrant_port=settings.QDRANT_PORT,
        total_points=total,
        is_healthy=is_healthy,
    )

    return APIResponse(
        success=is_healthy,
        data=data,
        request_id=request_id,
    )


@router.post("", response_model=APIResponse[SearchResponse])
async def search(
    request: Request,
    body: SearchRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Perform semantic, keyword, or hybrid search across the current user's indexed chunks."""
    request_id = getattr(request.state, "request_id", None)

    # Resolve allowed document IDs for the current user
    doc_stmt = select(Document.id).where(Document.user_id == current_user.id)
    if body.document_id:
        doc_stmt = doc_stmt.where(Document.id == body.document_id)
    user_doc_ids = set((await session.execute(doc_stmt)).scalars().all())
    if body.document_id and not user_doc_ids:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    if body.search_type == "keyword":
        results = await search_chunks_keywords(
            session=session,
            query=body.query,
            top_k=body.top_k,
            document_id=body.document_id,
            document_ids=list(user_doc_ids) if not body.document_id else None,
        )
    elif body.search_type == "semantic":
        provider = get_embedding_provider()
        query_vectors = await provider.embed([body.query])
        if not query_vectors or not query_vectors[0]:
            raise HTTPException(status_code=500, detail="Failed to embed query")
        results = await search_similar(
            query_vector=query_vectors[0],
            top_k=body.top_k,
            document_id=body.document_id,
            score_threshold=body.score_threshold,
        )
    else:
        results = await hybrid_search(
            query=body.query,
            top_k=body.top_k,
            document_id=body.document_id,
            score_threshold=body.score_threshold,
            session=session,
            rrf_k=body.rrf_k,
            rerank=body.rerank,
        )

    # Enforce user isolation on vector/hybrid results
    if body.search_type != "keyword":
        results = [r for r in results if r.get("document_id") in user_doc_ids]

    data = SearchResponse(
        query=body.query,
        results=[SearchResult(**r) for r in results[: body.top_k]],
        total_results=len(results),
    )

    return APIResponse(
        success=True,
        data=data,
        request_id=request_id,
    )


@router.post("/sync/{document_id}", response_model=APIResponse[SyncDocumentResponse])
async def sync_document_to_qdrant(
    request: Request,
    document_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync a document's embedded chunks to Qdrant.

    Existing points for this document are deleted first to avoid duplicates.
    """
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

    result = await session.execute(
        select(Chunk).where(
            Chunk.document_id == document_id,
            Chunk.embedding.isnot(None),
        )
    )
    chunks = result.scalars().all()

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No embedded chunks found for this document.",
        )

    # Delete existing points for this document
    await delete_document_chunks(document_id)

    # Prepare points
    chunk_points = [
        {
            "id": c.id,
            "document_id": c.document_id,
            "text": c.text,
            "source": c.source,
            "index": c.index,
            "embedding": deserialize_embedding(c.embedding),
            "start_char": c.start_char,
            "end_char": c.end_char,
        }
        for c in chunks
    ]

    synced = await upsert_chunk_points(chunk_points)

    data = SyncDocumentResponse(
        document_id=document_id,
        points_synced=synced,
        message=f"Synced {synced} chunks to Qdrant.",
    )

    return APIResponse(
        success=True,
        data=data,
        request_id=request_id,
    )
