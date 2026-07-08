"""
Document upload and management endpoints.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_settings
from app.core.config import Settings
from app.core.logging import get_logger
from app.db.base import get_db
from app.db.models import Chunk, Document, User
from app.models.document import (
    DocumentActionResponse,
    DocumentOut,
    DocumentUploadResponse,
    URLIngestRequest,
    URLIngestResponse,
)
from app.models.response import APIResponse
from app.services.document_service import (
    embed_chunks_for_document,
    save_from_url,
    save_upload,
    validate_upload,
)
from app.services.vector_store import delete_document_chunks

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = get_logger("documents_api")


@router.post("/upload", response_model=APIResponse[DocumentUploadResponse])
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(get_current_user),
):
    """Upload a PDF document for indexing.

    The file is validated, saved to disk, text is extracted, and a database
    record is created. Future days will add chunking + vector indexing.
    """
    request_id = getattr(request.state, "request_id", None)

    # Read file into memory
    file_bytes = await file.read()

    is_valid, error_msg = validate_upload(
        filename=file.filename or "unknown.pdf",
        content_type=file.content_type or "application/octet-stream",
        size=len(file_bytes),
    )

    if not is_valid:
        logger.warning("Upload rejected: %s", error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    document = await save_upload(
        session=session,
        filename=file.filename or "unknown.pdf",
        content_type=file.content_type or "application/pdf",
        file_bytes=file_bytes,
        user_id=current_user.id,
    )

    data = DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        content_type=document.content_type,
        file_size=document.file_size,
        status=document.status,
        created_at=document.created_at,
    )

    return APIResponse(
        success=document.status == "indexed",
        data=data,
        message=(
            "Document uploaded and indexed."
            if document.status == "indexed"
            else "Upload succeeded but text extraction failed."
        ),
        request_id=request_id,
    )


@router.post("/url", response_model=APIResponse[URLIngestResponse])
async def ingest_url(
    request: Request,
    body: URLIngestRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ingest a web page by URL for indexing.

    The page is fetched, article text is extracted, and a database record is
    created. Future days will add chunking + vector indexing.
    """
    request_id = getattr(request.state, "request_id", None)
    url = str(body.url)

    logger.info("URL ingestion requested: %s", url)

    document = await save_from_url(session=session, url=url, user_id=current_user.id)

    data = URLIngestResponse(
        id=document.id,
        filename=document.filename,
        url=document.file_path,
        title=document.filename,
        text_length=len(document.extracted_text or ""),
        status=document.status,
        created_at=document.created_at,
    )

    return APIResponse(
        success=document.status == "indexed",
        data=data,
        message=(
            "URL ingested and indexed."
            if document.status == "indexed"
            else "URL ingestion failed."
        ),
        request_id=request_id,
    )


@router.get("", response_model=APIResponse[list[DocumentOut]])
async def list_documents(
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List documents owned by the current user."""
    request_id = getattr(request.state, "request_id", None)

    result = await session.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    rows = result.scalars().all()

    return APIResponse(
        success=True,
        data=[DocumentOut.model_validate(r) for r in rows],
        request_id=request_id,
    )


@router.delete("/{document_id}", response_model=APIResponse[DocumentActionResponse])
async def delete_document(
    request: Request,
    document_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document, its chunks, and its Qdrant vectors."""
    request_id = getattr(request.state, "request_id", None)

    result = await session.execute(
        select(Document).where(
            Document.id == document_id, Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    filename = document.filename

    # Delete associated file if it's a local upload
    try:
        if document.content_type == "application/pdf":
            path = Path(document.file_path)
            if path.exists():
                path.unlink()
    except Exception as e:
        logger.warning("Failed to delete file %s: %s", document.file_path, e)

    # Delete Qdrant points
    try:
        await delete_document_chunks(document_id)
    except Exception as e:
        logger.warning("Failed to delete Qdrant points for %s: %s", document_id, e)

    # Delete DB record (cascades to chunks)
    await session.delete(document)
    await session.commit()

    logger.info("Deleted document %s", document_id)

    return APIResponse(
        success=True,
        data=DocumentActionResponse(
            id=document_id,
            action="delete",
            success=True,
            message=f"Deleted {filename}",
        ),
        request_id=request_id,
    )


@router.post(
    "/{document_id}/reindex", response_model=APIResponse[DocumentActionResponse]
)
async def reindex_document(
    request: Request,
    document_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-embed and re-sync a document to Qdrant."""
    request_id = getattr(request.state, "request_id", None)

    result = await session.execute(
        select(Document).where(
            Document.id == document_id, Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    if not document.extracted_text:
        raise HTTPException(status_code=400, detail="Document has no extractable text")

    # Delete existing chunks and embeddings
    await session.execute(
        Chunk.__table__.delete().where(Chunk.document_id == document_id)
    )
    await session.commit()

    # Delete Qdrant points
    try:
        await delete_document_chunks(document_id)
    except Exception as e:
        logger.warning("Failed to delete old Qdrant points for %s: %s", document_id, e)

    # Re-chunk and embed
    from app.services.chunking import chunk_document_async

    chunks = await chunk_document_async(
        text=document.extracted_text,
        document_id=document.id,
        source=document.filename,
    )

    for chunk in chunks:
        session.add(
            Chunk(
                id=chunk.id,
                document_id=chunk.document_id,
                index=chunk.index,
                text=chunk.text,
                source=chunk.source,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                parent_chunk_id=chunk.parent_chunk_id,
                level=chunk.level,
                chunk_strategy=chunk.strategy,
                metadata_json=chunk.metadata or None,
            )
        )
    await session.commit()

    # Embed and sync to Qdrant
    try:
        embedded = await embed_chunks_for_document(session, document_id)
        logger.info("Reindexed document %s with %d chunks", document_id, embedded)
        message = f"Reindexed {document.filename} ({embedded} chunks)"
    except Exception as e:
        logger.warning("Failed to sync embeddings to Qdrant for %s: %s", document_id, e)
        message = f"Reindexed {document.filename} in database, but vector sync failed"

    return APIResponse(
        success=True,
        data=DocumentActionResponse(
            id=document_id,
            action="reindex",
            success=True,
            message=message,
        ),
        request_id=request_id,
    )
