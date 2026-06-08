"""
Pydantic models for document API requests/responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response returned after a successful document upload."""

    id: str
    filename: str
    content_type: str
    file_size: int
    status: str
    created_at: datetime
    message: str = Field(default="Document uploaded successfully")


class DocumentOut(BaseModel):
    """Public document representation."""

    id: str
    filename: str
    content_type: str
    file_size: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
