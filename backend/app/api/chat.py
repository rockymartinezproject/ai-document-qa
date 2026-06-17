"""
Chat / RAG question-answering endpoints with conversation memory.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.base import get_db
from app.models.chat import ChatRequest, ChatResponse
from app.models.response import APIResponse
from app.services.chat_service import add_message, get_or_create_conversation
from app.services.rag import answer_question

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = get_logger("chat_api")


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
