"""Tests for chat conversation service functions."""

from app.services.chat_service import (
    add_message,
    count_messages,
    get_or_create_conversation,
    list_conversations,
)


async def test_create_conversation(db_session):
    conversation = await get_or_create_conversation(
        db_session, title="Test Chat", user_id="user-1"
    )
    assert conversation.title == "Test Chat"
    assert conversation.user_id == "user-1"


async def test_get_existing_conversation(db_session):
    created = await get_or_create_conversation(db_session, title="Existing")
    fetched = await get_or_create_conversation(
        db_session, conversation_id=created.id
    )
    assert fetched.id == created.id


async def test_add_message(db_session):
    conversation = await get_or_create_conversation(db_session)
    message = await add_message(
        db_session, conversation_id=conversation.id, role="user", content="Hello"
    )
    assert message.role == "user"
    assert message.content == "Hello"
    assert message.conversation_id == conversation.id


async def test_count_messages(db_session):
    conversation = await get_or_create_conversation(db_session)
    await add_message(db_session, conversation.id, "user", "One")
    await add_message(db_session, conversation.id, "assistant", "Two")
    assert await count_messages(db_session, conversation.id) == 2


async def test_list_conversations_by_user(db_session):
    await get_or_create_conversation(db_session, title="A", user_id="user-a")
    await get_or_create_conversation(db_session, title="B", user_id="user-b")

    a_convs = await list_conversations(db_session, user_id="user-a")
    assert len(a_convs) == 1
    assert a_convs[0].title == "A"
