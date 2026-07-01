"""
Pydantic models for chunk API responses.
"""

from datetime import datetime

from pydantic import BaseModel


from typing import Any, Dict, Optional


class ChunkOut(BaseModel):
    """Public chunk representation."""

    id: str
    document_id: str
    index: int
    text: str
    source: str
    start_char: int
    end_char: int
    parent_chunk_id: Optional[str] = None
    level: int = 0
    chunk_strategy: str = "recursive"
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
