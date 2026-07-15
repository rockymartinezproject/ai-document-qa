"""
Embedding provider abstraction with OpenAI + local fallback.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("embeddings")


class EmbeddingProvider(ABC):
    """Abstract base for embedding providers."""

    name: str = "unknown"
    dimension: int = 0

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts into vectors.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (one per input text).
        """
        ...


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI text-embedding-3-small provider."""

    name = "openai"
    dimension = 1536

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        import openai

        self._client = openai.AsyncOpenAI(
            api_key=api_key or settings.OPENAI_API_KEY,
            timeout=settings.REQUEST_TIMEOUT,
        )
        self._model = model or settings.EMBEDDING_MODEL

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        # Filter empty strings
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return [[] for _ in texts]

        logger.info(
            "Requesting OpenAI embeddings for %d texts (model=%s)",
            len(valid_texts),
            self._model,
        )

        response = await self._client.embeddings.create(
            model=self._model,
            input=valid_texts,
        )

        # Map back to original order (including empty strings)
        result_map = {}
        for item in response.data:
            result_map[item.index] = item.embedding

        return [result_map.get(i, []) for i in range(len(valid_texts))]


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local sentence-transformers fallback provider."""

    name = "local"
    dimension = 384  # all-MiniLM-L6-v2 default

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None

    def _load_model(self):
        """Lazy-load the sentence-transformers model."""
        if self._model is not None:
            return self._model

        from sentence_transformers import SentenceTransformer

        logger.info("Loading local embedding model: %s", self._model_name)
        self._model = SentenceTransformer(self._model_name)
        self.dimension = self._model.get_embedding_dimension() or 384
        logger.info(
            "Loaded local embedding model: %s (dim=%d)",
            self._model_name,
            self.dimension,
        )
        return self._model

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return [[] for _ in texts]

        logger.info(
            "Computing local embeddings for %d texts (model=%s)",
            len(valid_texts),
            self._model_name,
        )

        # Load model in background thread to avoid blocking event loop
        model = await asyncio.to_thread(self._load_model)

        # Encode in background thread
        embeddings = await asyncio.to_thread(
            model.encode,
            valid_texts,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        # Map back to original order
        result = []
        valid_idx = 0
        for t in texts:
            if t and t.strip():
                result.append(embeddings[valid_idx].tolist())
                valid_idx += 1
            else:
                result.append([])

        return result


# Singleton provider instance
_provider: Optional[EmbeddingProvider] = None


def get_embedding_provider() -> EmbeddingProvider:
    """Return the best available embedding provider.

    Tries OpenAI first if API key is configured, otherwise falls back to
    local sentence-transformers.
    """
    global _provider

    if _provider is not None:
        return _provider

    if settings.OPENAI_API_KEY:
        logger.info("Using OpenAI embedding provider")
        _provider = OpenAIEmbeddingProvider()
    else:
        logger.info("Using local embedding provider (sentence-transformers)")
        _provider = LocalEmbeddingProvider()

    return _provider


def clear_provider() -> None:
    """Clear the cached provider (useful for testing)."""
    global _provider
    _provider = None


def serialize_embedding(vector: List[float]) -> str:
    """Serialize a float vector to JSON string for DB storage."""
    return json.dumps(vector)


def deserialize_embedding(data: Optional[str]) -> List[float]:
    """Deserialize a JSON string back to float vector."""
    if not data:
        return []
    return json.loads(data)
