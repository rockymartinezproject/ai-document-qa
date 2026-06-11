"""
Pydantic models for embedding API responses.
"""

from pydantic import BaseModel, Field


class EmbeddingStatusResponse(BaseModel):
    """Status of embeddings for the system."""

    provider: str = Field(..., description="Active embedding provider name")
    dimension: int = Field(..., description="Embedding vector dimension")
    total_chunks: int = Field(..., description="Total chunks in database")
    embedded_chunks: int = Field(..., description="Chunks with embeddings computed")
    pending_chunks: int = Field(..., description="Chunks without embeddings")


class EmbedDocumentResponse(BaseModel):
    """Response after triggering embedding for a document."""

    document_id: str
    chunks_processed: int
    provider: str
    message: str
