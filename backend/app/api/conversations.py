"""
Conversation management endpoints.
"""

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.base import get_db
from app.models.chat import (
    ConversationDetailOut,
    ConversationOut,
    CreateConversationRequest,
    MessageOut,
    UpdateConversationRequest,
)
from app.models.response import APIResponse
from app.models.usage import ConversationUsageResponse, UsageRecordOut
from app.services.chat_service import (
    count_messages,
    delete_conversation,
    get_conversation_usage_totals,
    get_conversation_with_messages,
    get_usage_by_conversation,
    list_conversations,
    update_conversation_title,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])
logger = get_logger("conversations_api")


def _message_out(message) -> MessageOut:
    citations = None
    if message.citations:
        try:
            citations = json.loads(message.citations)
        except json.JSONDecodeError:
            citations = None

    return MessageOut(
        id=message.id,
        role=message.role,
        content=message.content,
        citations=citations,
        provider=message.provider,
        created_at=message.created_at,
    )


@router.get("", response_model=APIResponse[List[ConversationOut]])
async def get_conversations(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """List all chat conversations."""
    request_id = getattr(request.state, "request_id", None)

    conversations = await list_conversations(session)

    data = []
    for conv in conversations:
        msg_count = await count_messages(session, conv.id)
        data.append(
            ConversationOut(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=msg_count,
            )
        )

    return APIResponse(
        success=True,
        data=data,
        request_id=request_id,
    )


@router.post("", response_model=APIResponse[ConversationOut])
async def create_conversation(
    request: Request,
    body: CreateConversationRequest,
    session: AsyncSession = Depends(get_db),
):
    """Create a new empty conversation."""
    request_id = getattr(request.state, "request_id", None)

    from app.services.chat_service import get_or_create_conversation

    conversation = await get_or_create_conversation(
        session=session,
        title=body.title,
    )

    return APIResponse(
        success=True,
        data=ConversationOut(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=0,
        ),
        request_id=request_id,
    )


@router.get("/{conversation_id}", response_model=APIResponse[ConversationDetailOut])
async def get_conversation(
    request: Request,
    conversation_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    """Get a single conversation with paginated messages."""
    request_id = getattr(request.state, "request_id", None)

    result = await get_conversation_with_messages(
        session, conversation_id, limit=limit, offset=offset
    )
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation, messages = result

    data = ConversationDetailOut(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[_message_out(m) for m in messages],
    )

    return APIResponse(
        success=True,
        data=data,
        request_id=request_id,
    )


@router.put("/{conversation_id}", response_model=APIResponse[ConversationOut])
async def rename_conversation(
    request: Request,
    conversation_id: str,
    body: UpdateConversationRequest,
    session: AsyncSession = Depends(get_db),
):
    """Rename a conversation."""
    request_id = getattr(request.state, "request_id", None)

    conversation = await update_conversation_title(
        session=session,
        conversation_id=conversation_id,
        title=body.title,
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_count = await count_messages(session, conversation.id)
    return APIResponse(
        success=True,
        data=ConversationOut(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=msg_count,
        ),
        request_id=request_id,
    )


@router.get("/{conversation_id}/usage", response_model=APIResponse[ConversationUsageResponse])
async def conversation_usage(
    request: Request,
    conversation_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Return usage and cost records for a conversation."""
    request_id = getattr(request.state, "request_id", None)

    records = await get_usage_by_conversation(session, conversation_id)
    totals = await get_conversation_usage_totals(session, conversation_id)

    data = ConversationUsageResponse(
        conversation_id=conversation_id,
        total_input_tokens=totals["input_tokens"],
        total_output_tokens=totals["output_tokens"],
        total_cost=totals["cost"],
        records=[
            UsageRecordOut(
                id=r.id,
                conversation_id=r.conversation_id,
                message_id=r.message_id,
                model=r.model,
                input_tokens=r.input_tokens,
                output_tokens=r.output_tokens,
                cost=r.cost,
                created_at=r.created_at,
            )
            for r in records
        ],
    )

    return APIResponse(
        success=True,
        data=data,
        request_id=request_id,
    )


@router.delete("/{conversation_id}")
async def remove_conversation(
    request: Request,
    conversation_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Delete a conversation and its messages."""
    request_id = getattr(request.state, "request_id", None)

    deleted = await delete_conversation(session, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return APIResponse(
        success=True,
        data={"deleted": True},
        request_id=request_id,
    )
