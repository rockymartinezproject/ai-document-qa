"""
Pydantic models for usage/cost tracking API.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class UsageRecordOut(BaseModel):
    """Single usage/cost record."""

    id: str
    conversation_id: str
    message_id: Optional[str]
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    created_at: datetime


class ConversationUsageResponse(BaseModel):
    """Aggregated usage for a single conversation."""

    conversation_id: str
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    records: List[UsageRecordOut]


class TotalUsageResponse(BaseModel):
    """Aggregated usage across all conversations."""

    total_input_tokens: int
    total_output_tokens: int
    total_cost: float


class UsageBreakdownItem(BaseModel):
    """One row of a usage breakdown."""

    label: str
    input_tokens: int
    output_tokens: int
    cost: float
    count: int


class UsageBreakdownResponse(BaseModel):
    """Aggregated usage broken down by day, model, or conversation."""

    group_by: str
    days: Optional[int] = None
    items: List[UsageBreakdownItem]
