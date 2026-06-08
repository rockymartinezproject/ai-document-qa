"""
Document upload and management endpoints.
"""

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_settings
from app.core.config import Settings
from app.core.logging import get_logger
from app.db.base import get_db
from app.db.models import Document
from app.models.document import DocumentOut, DocumentUploadResponse
from app.models.response import APIResponse
from app.services.document_service import save_upload, validate_upload

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = get_logger("documents_api")


@router.post("/upload", response_model=APIResponse[DocumentUploadResponse])
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
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
        message="Document uploaded and indexed." if document.status == "indexed" else "Upload succeeded but text extraction failed.",
        request_id=request_id,
    )


@router.get("", response_model=APIResponse[list[DocumentOut]])
async def list_documents(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """List all uploaded documents."""
    request_id = getattr(request.state, "request_id", None)

    result = await session.execute(select(Document).order_by(Document.created_at.desc()))
    rows = result.scalars().all()

    return APIResponse(
        success=True,
        data=[DocumentOut.model_validate(r) for r in rows],
        request_id=request_id,
    )
