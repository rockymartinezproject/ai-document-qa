"""
Document upload business logic.
"""

import uuid
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models import Document
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.url_scraper import scrape_url

logger = get_logger("document_service")

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
}


def _ensure_upload_dir() -> Path:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def validate_upload(filename: str, content_type: str, size: int) -> Tuple[bool, str]:
    """Validate file metadata before saving."""
    if content_type not in ALLOWED_CONTENT_TYPES:
        return False, f"Unsupported file type: {content_type}. Only PDF is allowed."

    if not filename.lower().endswith(".pdf"):
        return False, "Only PDF files are supported."

    if size > settings.MAX_UPLOAD_SIZE:
        max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        return False, f"File exceeds maximum size of {max_mb:.0f}MB."

    if size == 0:
        return False, "File is empty."

    return True, ""


async def save_upload(
    session: AsyncSession,
    filename: str,
    content_type: str,
    file_bytes: bytes,
) -> Document:
    """Persist uploaded file to disk and create database record.

    Args:
        session: Async SQLAlchemy session.
        filename: Original file name.
        content_type: MIME type of the file.
        file_bytes: Raw file contents.

    Returns:
        Created Document database record.
    """
    upload_dir = _ensure_upload_dir()

    # Sanitize filename
    safe_name = Path(filename).name.replace(" ", "_")
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    file_path = upload_dir / unique_name

    # Write file to disk
    file_path.write_bytes(file_bytes)
    logger.info("Saved upload to %s", file_path)

    # Extract text
    extracted_text = await extract_text_from_pdf(file_bytes)
    status = "indexed" if extracted_text else "failed"

    # Create DB record
    document = Document(
        filename=safe_name,
        content_type=content_type,
        file_path=str(file_path),
        file_size=len(file_bytes),
        extracted_text=extracted_text,
        status=status,
        error_message=None if extracted_text else "Text extraction failed or PDF was empty.",
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)

    logger.info(
        "Created document record id=%s filename=%s status=%s",
        document.id,
        document.filename,
        document.status,
    )
    return document


async def save_from_url(
    session: AsyncSession,
    url: str,
) -> Document:
    """Scrape a URL and create a database record.

    Args:
        session: Async SQLAlchemy session.
        url: The web page URL to ingest.

    Returns:
        Created Document database record.
    """
    scraped = await scrape_url(url)

    if not scraped:
        # Create failed record
        document = Document(
            filename=Path(urlparse(url).path).name or "url_document",
            content_type="text/html",
            file_path=url,
            file_size=0,
            extracted_text=None,
            status="failed",
            error_message="Failed to scrape URL or content too short.",
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)
        return document

    status = "indexed"
    document = Document(
        filename=scraped["title"],
        content_type="text/html",
        file_path=scraped["url"],
        file_size=scraped["content_length"],
        extracted_text=scraped["text"],
        status=status,
        error_message=None,
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)

    logger.info(
        "Created URL document record id=%s title=%s status=%s",
        document.id,
        document.filename,
        document.status,
    )
    return document
