"""
Chat / RAG question-answering endpoints with conversation memory.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.base import get_db
from app.db.models import Conversation
from app.models.chat import ChatRequest, ChatResponse
from app.models.response import APIResponse
from app.services.chat_service import (
    add_message,
    generate_conversation_title,
    get_or_create_conversation,
    update_conversation_title,
)
from app.services.rag import answer_question, answer_question_stream

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = get_logger("chat_api")


async def _maybe_update_title(
    session: AsyncSession,
    conversation: Conversation,
    query: str,
    answer: str,
) -> None:
    """Generate and set a concise title for a new conversation."""
    try:
        title = await generate_conversation_title(
            session=session,
            conversation=conversation,
            query=query,
            answer=answer,
        )
        if title:
            await update_conversation_title(
                session=session,
                conversation_id=conversation.id,
                title=title,
            )
            conversation.title = title
    except Exception as e:
        logger.warning("Failed to update conversation title: %s", e)


@router.post("/ask", response_model=APIResponse[ChatResponse])
async def ask_question(
    request: Request,
    body: ChatRequest,
    session: AsyncSession = Depends(get_db),
):
    """Ask a question and get a grounded, cited answer.

    Creates a new conversation if no conversation_id is provided.
    Saves both user question and assistant answer to the conversation history.

    The pipeline:
    1. Embed the query
    2. Retrieve top-k similar chunks from Qdrant
    3. Build a RAG prompt with context
    4. Generate an answer with citations
    5. Persist messages to conversation history
    """
    request_id = getattr(request.state, "request_id", None)

    # Get or create conversation
    conversation = await get_or_create_conversation(
        session=session,
        conversation_id=body.conversation_id,
        title=body.query[:50] + "..." if len(body.query) > 50 else body.query,
    )

    # Save user message
    await add_message(
        session=session,
        conversation_id=conversation.id,
        role="user",
        content=body.query,
    )

    try:
        result = await answer_question(
            query=body.query,
            top_k=body.top_k,
            document_id=body.document_id,
            score_threshold=body.score_threshold,
            session=session,
            rerank=body.rerank,
        )
    except Exception as e:
        logger.error("RAG pipeline failed: %s", e)
        raise HTTPException(status_code=500, detail=f"RAG pipeline failed: {str(e)}")

    # Save assistant message
    await add_message(
        session=session,
        conversation_id=conversation.id,
        role="assistant",
        content=result.answer,
        citations=result.citations,
        provider=result.provider,
    )

    await _maybe_update_title(session, conversation, body.query, result.answer)

    data = ChatResponse(
        answer=result.answer,
        citations=[
            {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "source": c.source,
                "index": c.index,
                "text": c.text,
                "score": c.score,
            }
            for c in result.citations
        ],
        provider=result.provider,
        query=body.query,
        conversation_id=conversation.id,
    )

    return APIResponse(
        success=True,
        data=data,
        request_id=request_id,
    )


@router.post("/stream")
async def stream_answer(
    request: Request,
    body: ChatRequest,
    session: AsyncSession = Depends(get_db),
):
    """Ask a question and stream the answer as Server-Sent Events.

    Events:
      data: {"type": "citations", "citations": [...]}\n\n
      data: {"type": "token", "token": "..."}\n\n
      data: {"type": "done", "answer": "...", "citations": [...], "provider": "..."}\n\n

    The assistant message is persisted to conversation history when the stream
    finishes or the client disconnects.
    """
    request_id = getattr(request.state, "request_id", None)

    conversation = await get_or_create_conversation(
        session=session,
        conversation_id=body.conversation_id,
        title=body.query[:50] + "..." if len(body.query) > 50 else body.query,
    )

    await add_message(
        session=session,
        conversation_id=conversation.id,
        role="user",
        content=body.query,
    )

    async def event_generator():
        full_answer = ""
        final_answer = ""
        citations = []
        provider = "unknown"

        try:
            async for event in answer_question_stream(
                query=body.query,
                top_k=body.top_k,
                document_id=body.document_id,
                score_threshold=body.score_threshold,
                session=session,
                rerank=body.rerank,
            ):
                if event["type"] == "token":
                    full_answer += event["token"]
                elif event["type"] == "done":
                    final_answer = event.get("answer", full_answer)
                    citations = event.get("citations", [])
                    provider = event.get("provider", "unknown")

                payload = {
                    **event,
                    "request_id": request_id,
                }
                yield f"data: {json.dumps(payload)}\n\n"
        except Exception as e:
            logger.error("Streaming RAG pipeline failed: %s", e)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'request_id': request_id})}\n\n"
        finally:
            answer_to_save = final_answer or full_answer
            try:
                await add_message(
                    session=session,
                    conversation_id=conversation.id,
                    role="assistant",
                    content=answer_to_save,
                    citations=citations,
                    provider=provider,
                )
                await session.commit()
                await _maybe_update_title(
                    session=session,
                    conversation=conversation,
                    query=body.query,
                    answer=answer_to_save,
                )
            except Exception as save_err:
                logger.error("Failed to persist streamed assistant message: %s", save_err)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
