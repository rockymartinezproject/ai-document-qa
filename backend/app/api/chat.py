"""
Chat / RAG question-answering endpoints.
"""

from fastapi import APIRouter, HTTPException, Request

from app.core.logging import get_logger
from app.models.chat import ChatRequest, ChatResponse
from app.models.response import APIResponse
from app.services.rag import answer_question

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = get_logger("chat_api")


@router.post("/ask", response_model=APIResponse[ChatResponse])
async def ask_question(
    request: Request,
    body: ChatRequest,
):
    """Ask a question and get a grounded, cited answer.

    The pipeline:
    1. Embed the query
    2. Retrieve top-k similar chunks from Qdrant
    3. Build a RAG prompt with context
    4. Generate an answer with citations
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        result = await answer_question(
            query=body.query,
            top_k=body.top_k,
            document_id=body.document_id,
            score_threshold=body.score_threshold,
        )
    except Exception as e:
        logger.error("RAG pipeline failed: %s", e)
        raise HTTPException(status_code=500, detail=f"RAG pipeline failed: {str(e)}")

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
    )

    return APIResponse(
        success=True,
        data=data,
        request_id=request_id,
    )
