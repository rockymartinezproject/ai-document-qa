"""
Recursive character text chunking with overlap.

This is a from-scratch implementation of the algorithm used by
LangChain's RecursiveCharacterTextSplitter, demonstrating understanding
of how semantic chunking works under the hood.
"""

from dataclasses import dataclass
from typing import List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("chunking")

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass
class Chunk:
    """A single text chunk with metadata."""

    text: str
    index: int
    document_id: str
    source: str
    start_char: int
    end_char: int


def _split_text(text: str, separator: str) -> List[str]:
    """Split text by a separator, keeping the separator if it's meaningful."""
    if separator == "":
        return list(text)
    # Keep separator attached to the preceding segment for context
    parts = text.split(separator)
    # Re-attach separator to all but the last part
    result = []
    for i, part in enumerate(parts):
        if i < len(parts) - 1:
            result.append(part + separator)
        else:
            result.append(part)
    # Filter empty strings
    return [r for r in result if r]


def _merge_splits(
    splits: List[str],
    separator: str,
    chunk_size: int,
    chunk_overlap: int,
) -> List[str]:
    """Merge small splits into chunks of appropriate size with overlap."""
    chunks = []
    current_chunk = []
    current_length = 0

    for split in splits:
        split_length = len(split)

        # If a single split exceeds chunk_size, we can't fit it —
        # the caller should have used a smaller separator first.
        if split_length > chunk_size:
            # Force add it anyway; better than dropping content
            if current_chunk:
                chunks.append("".join(current_chunk).strip())
            chunks.append(split.strip())
            current_chunk = []
            current_length = 0
            continue

        # If adding this split would exceed chunk_size, finalize current chunk
        if current_length + split_length > chunk_size and current_chunk:
            chunks.append("".join(current_chunk).strip())
            # Build overlap: keep last splits that fit within chunk_overlap
            overlap_splits = []
            overlap_length = 0
            for s in reversed(current_chunk):
                if overlap_length + len(s) <= chunk_overlap:
                    overlap_splits.insert(0, s)
                    overlap_length += len(s)
                else:
                    break
            current_chunk = overlap_splits
            current_length = overlap_length

        current_chunk.append(split)
        current_length += split_length

    # Don't forget the last chunk
    if current_chunk:
        final = "".join(current_chunk).strip()
        if final:
            chunks.append(final)

    return chunks


def recursive_split(
    text: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    separators: Optional[List[str]] = None,
) -> List[str]:
    """Recursively split text into chunks using a hierarchy of separators.

    The algorithm tries large separators first (paragraph breaks), then
    progressively falls back to smaller ones (sentences, words, characters)
    when a chunk cannot be made to fit.

    Args:
        text: The full text to split.
        chunk_size: Target maximum characters per chunk.
        chunk_overlap: Characters to overlap between consecutive chunks.
        separators: Ordered list of separators to try.

    Returns:
        List of text chunks.
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    separators = separators or DEFAULT_SEPARATORS

    if not text or not text.strip():
        return []

    # Try each separator in order
    final_chunks = []

    def _recurse(remaining_text: str, separator_idx: int):
        if separator_idx >= len(separators):
            # Last resort: character splitting (should rarely happen)
            for i in range(0, len(remaining_text), chunk_size):
                final_chunks.append(remaining_text[i : i + chunk_size])
            return

        separator = separators[separator_idx]
        splits = _split_text(remaining_text, separator)

        # If all splits fit in chunk_size, merge them nicely
        if all(len(s) <= chunk_size for s in splits):
            merged = _merge_splits(splits, separator, chunk_size, chunk_overlap)
            final_chunks.extend(merged)
            return

        # Some splits are too big — recurse on each oversized split
        buffer = []
        buffer_len = 0
        for split in splits:
            if len(split) > chunk_size:
                # Flush buffer first
                if buffer:
                    merged = _merge_splits(buffer, separator, chunk_size, chunk_overlap)
                    final_chunks.extend(merged)
                    buffer = []
                    buffer_len = 0
                _recurse(split, separator_idx + 1)
            else:
                buffer.append(split)
                buffer_len += len(split)

        if buffer:
            merged = _merge_splits(buffer, separator, chunk_size, chunk_overlap)
            final_chunks.extend(merged)

    _recurse(text.strip(), 0)

    # Deduplicate and filter empty
    seen = set()
    result = []
    for chunk in final_chunks:
        key = chunk.strip()
        if key and key not in seen:
            seen.add(key)
            result.append(key)

    logger.info(
        "Split %d characters into %d chunks (size=%d, overlap=%d)",
        len(text),
        len(result),
        chunk_size,
        chunk_overlap,
    )
    return result


def chunk_document(
    text: str,
    document_id: str,
    source: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> List[Chunk]:
    """Split document text into Chunk objects with metadata.

    Args:
        text: Full extracted text.
        document_id: Parent document UUID.
        source: Human-readable source identifier (filename or URL).
        chunk_size: Target chunk size.
        chunk_overlap: Overlap size.

    Returns:
        List of Chunk dataclasses.
    """
    texts = recursive_split(text, chunk_size, chunk_overlap)
    chunks = []
    cursor = 0

    for i, chunk_text in enumerate(texts):
        start = text.find(chunk_text, cursor)
        if start == -1:
            start = cursor
        end = start + len(chunk_text)
        cursor = max(cursor, end - (chunk_overlap or settings.CHUNK_OVERLAP))

        chunks.append(
            Chunk(
                text=chunk_text,
                index=i,
                document_id=document_id,
                source=source,
                start_char=start,
                end_char=end,
            )
        )

    return chunks
