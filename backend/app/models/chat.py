"""
Pydantic models for chat API.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for asking a question."""

    query: str = Field(..., min_length=1, description="User question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    document_id: Optional[str] = Field(default=None, description="Optional document filter")
    score_threshold: Optional[float] = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for retrieved chunks",
    )
    search_type: Literal["semantic", "keyword", "hybrid"] = Field(
        default="hybrid",
        description="Retrieval mode: semantic, keyword, or hybrid",
    )
    rerank: bool = Field(
        default=True,
        description="Apply configured reranker to retrieved chunks",
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Existing conversation ID (creates new thread if omitted)",
    )
    provider: Optional[str] = Field(
        default=None,
        description="LLM provider to use (openai, anthropic, ollama, mock). Uses default if omitted.",
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific model name to use; falls back to provider default if omitted.",
    )


class CitationOut(BaseModel):
    """Citation included in a chat response."""

    chunk_id: str
    document_id: str
    source: str
    index: int
    text: str
    score: float
    parent_chunk_id: Optional[str] = None
    level: int = 0
    chunk_strategy: str = "recursive"
    metadata_json: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response to a chat question."""

    answer: str
    citations: List[CitationOut]
    provider: str
    query: str
    conversation_id: str


class MessageOut(BaseModel):
    """Single message in a conversation."""

    id: str
    role: str
    content: str
    citations: Optional[List[CitationOut]] = None
    provider: Optional[str] = None
    created_at: datetime


class ConversationOut(BaseModel):
    """Conversation thread without messages."""

    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ConversationDetailOut(BaseModel):
    """Conversation thread with messages."""

    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageOut]


class CreateConversationRequest(BaseModel):
    title: Optional[str] = None


class UpdateConversationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=512, description="New conversation title")
