"""
Pydantic models for vector/search API.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request body for search."""

    query: str = Field(..., min_length=1, description="Natural language query")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")
    document_id: Optional[str] = Field(default=None, description="Filter by document ID")
    score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity score for vector results",
    )
    search_type: Literal["semantic", "keyword", "hybrid"] = Field(
        default="hybrid",
        description="Search mode: semantic (vector only), keyword (BM25), or hybrid (RRF fusion)",
    )
    rrf_k: int = Field(
        default=60,
        ge=1,
        le=200,
        description="Reciprocal rank fusion constant",
    )
    rerank: bool = Field(
        default=True,
        description="Apply configured reranker to fused results",
    )


class SearchResult(BaseModel):
    """Single search result."""

    id: str
    score: float
    document_id: str
    text: str
    source: str
    index: int
    start_char: int
    end_char: int


class SearchResponse(BaseModel):
    """Response from search."""

    query: str
    results: list[SearchResult]
    total_results: int


class SyncDocumentResponse(BaseModel):
    """Response after syncing a document to Qdrant."""

    document_id: str
    points_synced: int
    message: str


class VectorStoreStatusResponse(BaseModel):
    """Vector store status."""

    collection_name: str
    qdrant_host: str
    qdrant_port: int
    total_points: int
    is_healthy: bool
