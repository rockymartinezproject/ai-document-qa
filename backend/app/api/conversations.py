"""
Conversation management endpoints.
"""

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.base import get_db
from app.models.chat import (
    ConversationDetailOut,
    ConversationOut,
    CreateConversationRequest,
    MessageOut,
)
from app.models.response import APIResponse
from app.services.chat_service import (
    count_messages,
    delete_conversation,
    get_conversation_with_messages,
    get_messages,
    list_conversations,
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
    session: AsyncSession = Depends(get_db),
):
    """Get a single conversation with all messages."""
    request_id = getattr(request.state, "request_id", None)

    result = await get_conversation_with_messages(session, conversation_id)
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


@router.delete("/{conversation_id}")
async def remove_conversation(
    request: Request,
    conversation_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    request_id = getattr(request.state, "request_id", None)

    deleted = await delete_conversation(session, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return APIResponse(
        success=True,
        data={"deleted": True},
        request_id=request_id,
    )
