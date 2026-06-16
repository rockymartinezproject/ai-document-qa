"""
Qdrant vector database integration.
"""

from typing import Any, Dict, List, Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointIdsList,
    PointStruct,
    VectorParams,
)

from app.core.config import settings
from app.core.logging import get_logger
from app.services.embeddings import get_embedding_provider

logger = get_logger("vector_store")

# Singleton client
_client: Optional[AsyncQdrantClient] = None


def get_qdrant_client() -> AsyncQdrantClient:
    """Return singleton Qdrant client."""
    global _client
    if _client is None:
        _client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            timeout=settings.QDRANT_TIMEOUT,
        )
    return _client


def get_collection_name() -> str:
    return settings.QDRANT_COLLECTION_NAME


async def ensure_collection(dimension: Optional[int] = None) -> None:
    """Create Qdrant collection if it doesn't exist.

    Args:
        dimension: Vector dimension. Defaults to active embedding provider dimension.
    """
    client = get_qdrant_client()
    collection_name = get_collection_name()

    if dimension is None:
        provider = get_embedding_provider()
        dimension = provider.dimension

    try:
        collections = await client.get_collections()
        exists = any(c.name == collection_name for c in collections.collections)

        if not exists:
            logger.info(
                "Creating Qdrant collection '%s' with dimension %d",
                collection_name,
                dimension,
            )
            await client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Qdrant collection created")
        else:
            logger.debug("Qdrant collection '%s' already exists", collection_name)
    except Exception as e:
        logger.error("Failed to ensure Qdrant collection: %s", e)
        raise


async def upsert_chunk_points(
    chunks: List[Dict[str, Any]],
) -> int:
    """Upsert chunk vectors and metadata into Qdrant.

    Args:
        chunks: List of dicts with id, document_id, text, source, index,
            embedding (list of floats), start_char, end_char.

    Returns:
        Number of points upserted.
    """
    await ensure_collection()
    client = get_qdrant_client()
    collection_name = get_collection_name()

    points = [
        PointStruct(
            id=chunk["id"],
            vector=chunk["embedding"],
            payload={
                "document_id": chunk["document_id"],
                "text": chunk["text"],
                "source": chunk["source"],
                "index": chunk["index"],
                "start_char": chunk["start_char"],
                "end_char": chunk["end_char"],
            },
        )
        for chunk in chunks
        if chunk.get("embedding")
    ]

    if not points:
        logger.warning("No valid chunk points to upsert")
        return 0

    await client.upsert(
        collection_name=collection_name,
        points=points,
        wait=True,
    )

    logger.info("Upserted %d chunk points to Qdrant", len(points))
    return len(points)


async def search_similar(
    query_vector: List[float],
    top_k: int = 5,
    document_id: Optional[str] = None,
    score_threshold: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Search for similar chunks in Qdrant.

    Args:
        query_vector: Query embedding vector.
        top_k: Number of results to return.
        document_id: Optional filter by document ID.
        score_threshold: Optional minimum similarity score.

    Returns:
        List of search results with id, score, and payload.
    """
    await ensure_collection()
    client = get_qdrant_client()
    collection_name = get_collection_name()

    filters = []
    if document_id:
        filters.append(
            FieldCondition(
                key="document_id",
                match=MatchValue(value=document_id),
            )
        )

    search_filter = Filter(must=filters) if filters else None

    results = await client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
        query_filter=search_filter,
        score_threshold=score_threshold,
        with_payload=True,
    )

    return [
        {
            "id": r.id,
            "score": r.score,
            "document_id": r.payload.get("document_id"),
            "text": r.payload.get("text"),
            "source": r.payload.get("source"),
            "index": r.payload.get("index"),
            "start_char": r.payload.get("start_char"),
            "end_char": r.payload.get("end_char"),
        }
        for r in results
    ]


async def delete_document_chunks(document_id: str) -> int:
    """Delete all Qdrant points for a given document.

    Args:
        document_id: Document UUID.

    Returns:
        Number of points deleted.
    """
    client = get_qdrant_client()
    collection_name = get_collection_name()

    points, _ = await client.scroll(
        collection_name=collection_name,
        scroll_filter=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
        limit=1000,
        with_payload=False,
    )

    if not points:
        return 0

    ids = [p.id for p in points]
    await client.delete(
        collection_name=collection_name,
        points_selector=PointIdsList(points=ids),
        wait=True,
    )

    logger.info("Deleted %d Qdrant points for document %s", len(ids), document_id)
    return len(ids)


async def count_points() -> int:
    """Return total number of points in the collection."""
    client = get_qdrant_client()
    collection_name = get_collection_name()

    try:
        count = await client.count(collection_name=collection_name)
        return count.count
    except Exception as e:
        logger.error("Failed to count Qdrant points: %s", e)
        return 0
