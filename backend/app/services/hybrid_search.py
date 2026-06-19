"""
Hybrid search: combine vector similarity and keyword search using reciprocal rank fusion,
with optional cross-encoder / Cohere reranking.
"""

import asyncio
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.services.embeddings import get_embedding_provider
from app.services.keyword_search import search_chunks_keywords
from app.services.reranker import get_reranker
from app.services.vector_store import search_similar

logger = get_logger("hybrid_search")

DEFAULT_RRF_K = 60


def _reciprocal_rank_fusion(
    vector_results: List[Dict[str, Any]],
    keyword_results: List[Dict[str, Any]],
    k: int = DEFAULT_RRF_K,
) -> List[Dict[str, Any]]:
    """Fuse two ranked result lists using Reciprocal Rank Fusion (RRF).

    Score = sum(1 / (k + rank)) for each list where the item appears.
    """
    fused: Dict[str, Dict[str, Any]] = {}

    def _add(results: List[Dict[str, Any]]) -> None:
        for rank, item in enumerate(results, start=1):
            item_id = item["id"]
            entry = fused.get(item_id)
            if entry is None:
                entry = {"item": item, "score": 0.0}
                fused[item_id] = entry
            entry["score"] += 1.0 / (k + rank)

    _add(vector_results)
    _add(keyword_results)

    sorted_entries = sorted(fused.values(), key=lambda e: e["score"], reverse=True)
    return [
        {
            **entry["item"],
            "score": round(entry["score"], 6),
        }
        for entry in sorted_entries
    ]


async def _safe_vector_search(
    query: str,
    top_k: int,
    document_id: Optional[str],
    score_threshold: Optional[float],
) -> List[Dict[str, Any]]:
    """Run vector search and return empty results on failure."""
    try:
        provider = get_embedding_provider()
        query_vectors = await provider.embed([query])
        if not query_vectors or not query_vectors[0]:
            logger.warning("Failed to embed query for vector search")
            return []
        return await search_similar(
            query_vector=query_vectors[0],
            top_k=top_k,
            document_id=document_id,
            score_threshold=score_threshold,
        )
    except Exception as e:
        logger.warning("Vector search failed, falling back to keyword search: %s", e)
        return []


def _candidate_top_k(final_top_k: int) -> int:
    """Retrieve enough candidates to give the reranker a meaningful pool."""
    return max(final_top_k * 4, 20)


async def hybrid_search(
    query: str,
    top_k: int = 5,
    document_id: Optional[str] = None,
    score_threshold: Optional[float] = None,
    session: Optional[AsyncSession] = None,
    rrf_k: int = DEFAULT_RRF_K,
    rerank: bool = True,
) -> List[Dict[str, Any]]:
    """Run hybrid search: vector + keyword fused with RRF, then reranked.

    If vector search fails (e.g. Qdrant unavailable), keyword results are used alone.
    If no session is provided, keyword search is skipped.
    If reranking is disabled or the configured reranker fails to load, the RRF
    fused results are returned.

    Args:
        query: Natural language query.
        top_k: Number of top results to return.
        document_id: Optional document filter.
        score_threshold: Minimum vector similarity score.
        session: Async SQLAlchemy session for keyword search.
        rrf_k: RRF rank constant.
        rerank: Whether to apply the configured reranker.

    Returns:
        Merged, reranked list of chunk results.
    """
    candidate_k = _candidate_top_k(top_k)

    vector_task = asyncio.create_task(
        _safe_vector_search(query, candidate_k, document_id, score_threshold)
    )

    if session is not None:
        keyword_task = asyncio.create_task(
            search_chunks_keywords(session, query, top_k=candidate_k, document_id=document_id)
        )
        vector_results, keyword_results = await asyncio.gather(vector_task, keyword_task)
    else:
        vector_results = await vector_task
        keyword_results = []

    fused = _reciprocal_rank_fusion(vector_results, keyword_results, k=rrf_k)
    candidates = fused[:candidate_k]

    if not candidates or not rerank:
        return candidates[:top_k]

    try:
        reranker = get_reranker()
        passages = [c["text"] for c in candidates]
        ranked = await reranker.rerank(query, passages, top_k=top_k)
        logger.info("Reranked %d candidates to top %d", len(candidates), len(ranked))
        return [
            {
                **candidates[idx],
                "score": round(score, 6),
            }
            for idx, score in ranked
        ]
    except Exception as e:
        logger.warning("Reranking failed: %s. Returning fused results.", e)
        return candidates[:top_k]
