"""
Chat conversation persistence service.
"""

import json
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import Conversation, Message
from app.services.rag import Citation

logger = get_logger("chat_service")


async def get_or_create_conversation(
    session: AsyncSession,
    conversation_id: Optional[str] = None,
    title: Optional[str] = None,
) -> Conversation:
    """Get existing conversation or create a new one."""
    if conversation_id:
        result = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            return conversation

    conversation = Conversation(title=title or "New Chat")
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    logger.info("Created conversation %s", conversation.id)
    return conversation


async def add_message(
    session: AsyncSession,
    conversation_id: str,
    role: str,
    content: str,
    citations: Optional[List[Citation]] = None,
    provider: Optional[str] = None,
) -> Message:
    """Add a message to a conversation."""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        citations=json.dumps([c.__dict__ for c in citations]) if citations else None,
        provider=provider,
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def list_conversations(
    session: AsyncSession,
    limit: int = 50,
) -> List[Conversation]:
    """List recent conversations."""
    result = await session.execute(
        select(Conversation)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_conversation_with_messages(
    session: AsyncSession,
    conversation_id: str,
) -> Optional[tuple[Conversation, List[Message]]]:
    """Get a conversation and all its messages."""
    conv_result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        return None

    msg_result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()

    return conversation, list(messages)


async def count_messages(
    session: AsyncSession,
    conversation_id: str,
) -> int:
    """Count messages in a conversation."""
    from sqlalchemy import func

    result = await session.execute(
        select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
    )
    return result.scalar() or 0


async def get_messages(
    session: AsyncSession,
    conversation_id: str,
) -> List[Message]:
    """Get all messages for a conversation."""
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    return result.scalars().all()


async def update_conversation_title(
    session: AsyncSession,
    conversation_id: str,
    title: str,
) -> Optional[Conversation]:
    """Update conversation title."""
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation:
        conversation.title = title
        await session.commit()
        await session.refresh(conversation)
    return conversation


async def delete_conversation(
    session: AsyncSession,
    conversation_id: str,
) -> bool:
    """Delete a conversation and its messages."""
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        return False

    await session.delete(conversation)
    await session.commit()
    return True
