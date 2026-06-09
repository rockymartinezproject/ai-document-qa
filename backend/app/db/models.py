"""
SQLAlchemy models for persistent entities.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.db.base import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Document(Base):
    """Represents an uploaded document."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(512), nullable=False)
    content_type = Column(String(128), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=False)
    extracted_text = Column(Text, nullable=True)
    status = Column(String(32), default="pending", nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)


class Chunk(Base):
    """Represents a text chunk from a document."""

    __tablename__ = "chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    source = Column(String(512), nullable=False)
    start_char = Column(Integer, nullable=False)
    end_char = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)
