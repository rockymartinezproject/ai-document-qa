"""
PDF text extraction utilities.
"""

import io
from typing import Optional

import pdfplumber

from app.core.logging import get_logger

logger = get_logger("pdf_extractor")


async def extract_text_from_pdf(file_bytes: bytes) -> Optional[str]:
    """Extract plain text from PDF bytes using pdfplumber.

    Args:
        file_bytes: Raw PDF file contents.

    Returns:
        Extracted text or None if extraction fails.
    """
    text_parts = []

    try:
        with io.BytesIO(file_bytes) as buffer, pdfplumber.open(buffer) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                try:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_parts.append(f"\n--- Page {i} ---\n{page_text}")
                except Exception as e:
                    logger.warning("Failed to extract page %d: %s", i, e)
                    continue
    except Exception as e:
        logger.error("Failed to open PDF: %s", e)
        return None

    full_text = "\n".join(text_parts).strip()
    logger.info("Extracted %d characters from PDF", len(full_text))
    return full_text if full_text else None
