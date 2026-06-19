"""
Re-ranking service: refine retrieval results using a cross-encoder or Cohere API.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("reranker")


class Reranker(ABC):
    """Abstract reranker."""

    name: str = "unknown"

    @abstractmethod
    async def rerank(
        self,
        query: str,
        passages: List[str],
        top_k: Optional[int] = None,
    ) -> List[tuple[int, float]]:
        """Return (original_index, score) pairs sorted by descending score."""
        ...


class CrossEncoderReranker(Reranker):
    """Local cross-encoder reranker (e.g. ms-marco-MiniLM)."""

    name = "cross_encoder"

    def __init__(self, model_name: Optional[str] = None):
        from sentence_transformers import CrossEncoder

        self.model_name = model_name or settings.CROSS_ENCODER_MODEL
        logger.info("Loading cross-encoder reranker: %s", self.model_name)
        self._model = CrossEncoder(self.model_name)

    async def rerank(
        self,
        query: str,
        passages: List[str],
        top_k: Optional[int] = None,
    ) -> List[tuple[int, float]]:
        if not passages:
            return []

        pairs = [[query, passage] for passage in passages]
        scores = self._model.predict(pairs, convert_to_numpy=True)
        ranked = sorted(
            ((i, float(scores[i])) for i in range(len(passages))),
            key=lambda x: x[1],
            reverse=True,
        )
        if top_k:
            ranked = ranked[:top_k]
        return ranked


class CohereReranker(Reranker):
    """Cohere Rerank API reranker."""

    name = "cohere"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.COHERE_API_KEY
        self.model = settings.COHERE_RERANK_MODEL

    async def rerank(
        self,
        query: str,
        passages: List[str],
        top_k: Optional[int] = None,
    ) -> List[tuple[int, float]]:
        if not passages or not self.api_key:
            return []

        url = "https://api.cohere.com/v2/rerank"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "query": query,
            "documents": passages,
            "top_n": top_k or len(passages),
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        results = data.get("results", [])
        ranked = [
            (r["index"], float(r["relevance_score"]))
            for r in sorted(results, key=lambda x: x["index"])
        ]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked


class NoopReranker(Reranker):
    """Fallback reranker that preserves input order."""

    name = "none"

    async def rerank(
        self,
        query: str,
        passages: List[str],
        top_k: Optional[int] = None,
    ) -> List[tuple[int, float]]:
        ranked = [(i, 0.0) for i in range(len(passages))]
        if top_k:
            ranked = ranked[:top_k]
        return ranked


_reranker: Optional[Reranker] = None


def get_reranker() -> Reranker:
    """Return singleton reranker based on config."""
    global _reranker
    if _reranker is None:
        provider = settings.RERANK_PROVIDER.lower()
        if not settings.RERANK_ENABLED or provider == "none":
            logger.info("Reranking disabled")
            _reranker = NoopReranker()
        elif provider == "cohere":
            if settings.COHERE_API_KEY:
                logger.info("Using Cohere reranker")
                _reranker = CohereReranker()
            else:
                logger.warning("Cohere reranker configured but no API key; disabling reranking")
                _reranker = NoopReranker()
        else:
            try:
                logger.info("Using cross-encoder reranker")
                _reranker = CrossEncoderReranker()
            except Exception as e:
                logger.warning("Failed to load cross-encoder reranker: %s. Disabling reranking.", e)
                _reranker = NoopReranker()
    return _reranker


def clear_reranker() -> None:
    """Clear cached reranker (useful for testing)."""
    global _reranker
    _reranker = None
