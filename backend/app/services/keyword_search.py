"""
Keyword/BM25-style search over indexed chunks in SQLite.
"""

import re
from typing import Any, Dict, List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import Chunk

logger = get_logger("keyword_search")


def _tokenize(text: str) -> List[str]:
    """Extract lowercase alphanumeric tokens from text."""
    return [t for t in re.findall(r"\w+", text.lower()) if len(t) > 1]


async def search_chunks_keywords(
    session: AsyncSession,
    query: str,
    top_k: int = 10,
    document_id: Optional[str] = None,
    document_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Search chunk text with simple keyword/BM25-style scoring.

    Args:
        session: Async SQLAlchemy session.
        query: User query.
        top_k: Maximum number of results.
        document_id: Optional single document filter.
        document_ids: Optional list of allowed document IDs (user isolation).

    Returns:
        List of result dicts with the same shape as vector search results.
    """
    tokens = _tokenize(query)
    if not tokens:
        return []

    conditions = [Chunk.text.ilike(f"%{token}%") for token in tokens]
    stmt = select(Chunk).where(or_(*conditions))
    if document_id:
        stmt = stmt.where(Chunk.document_id == document_id)
    elif document_ids:
        stmt = stmt.where(Chunk.document_id.in_(document_ids))

    result = await session.execute(stmt)
    chunks = result.scalars().all()

    scored: List[Dict[str, Any]] = []
    for chunk in chunks:
        text_lower = chunk.text.lower()
        term_frequencies = [text_lower.count(token) for token in tokens]
        matched_terms = sum(1 for tf in term_frequencies if tf > 0)
        total_tf = sum(term_frequencies)
        word_count = max(len(text_lower.split()), 1)

        # Simple BM25-ish score: reward matched distinct terms + normalized tf
        score = matched_terms + (total_tf / word_count)

        scored.append(
            {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "text": chunk.text,
                "source": chunk.source,
                "index": chunk.index,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "parent_chunk_id": chunk.parent_chunk_id,
                "level": chunk.level,
                "chunk_strategy": chunk.chunk_strategy,
                "metadata_json": chunk.metadata_json,
                "score": score,
            }
        )

    scored.sort(key=lambda r: r["score"], reverse=True)
    logger.info("Keyword search found %d chunks for query", len(scored))
    return scored[:top_k]
