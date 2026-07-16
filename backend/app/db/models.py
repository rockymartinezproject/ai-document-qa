"""
SQLAlchemy models for persistent entities.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)

from app.db.base import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """Registered application user."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)


class Document(Base):
    """Represents an uploaded document."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    filename = Column(String(512), nullable=False)
    content_type = Column(String(128), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=False)
    extracted_text = Column(Text, nullable=True)
    status = Column(String(32), default="pending", nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now_utc, nullable=False)


class UsageRecord(Base):
    """Tracks token usage and estimated cost for an assistant response."""

    __tablename__ = "usage_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    message_id = Column(
        String(36), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    model = Column(String(128), nullable=False)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)


class Chunk(Base):
    """Represents a text chunk from a document."""

    __tablename__ = "chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    source = Column(String(512), nullable=False)
    start_char = Column(Integer, nullable=False)
    end_char = Column(Integer, nullable=False)
    embedding = Column(Text, nullable=True)  # JSON serialized vector
    embedding_model = Column(String(128), nullable=True)
    parent_chunk_id = Column(
        String(36), ForeignKey("chunks.id", ondelete="CASCADE"), nullable=True
    )
    level = Column(Integer, default=0, nullable=False)
    chunk_strategy = Column(String(32), default="recursive", nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=now_utc, nullable=False)


class Conversation(Base):
    """Represents a chat conversation thread."""

    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)


class Message(Base):
    """Represents a single message in a conversation."""

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String(32), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    citations = Column(Text, nullable=True)  # JSON serialized
    provider = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=now_utc, nullable=False)


class EvaluationRun(Base):
    """Stores the results of an evaluation run."""

    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(256), nullable=False)
    status = Column(String(32), default="pending", nullable=False)
    sample_count = Column(Integer, default=0, nullable=False)
    samples = Column(JSON, nullable=True)
    results = Column(JSON, nullable=True)
    aggregate = Column(JSON, nullable=True)
    regression = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)
