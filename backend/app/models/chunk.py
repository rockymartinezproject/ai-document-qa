"""
Pydantic models for chunk API responses.
"""

from datetime import datetime

from pydantic import BaseModel


class ChunkOut(BaseModel):
    """Public chunk representation."""

    id: str
    document_id: str
    index: int
    text: str
    source: str
    start_char: int
    end_char: int
    created_at: datetime

    class Config:
        from_attributes = True
