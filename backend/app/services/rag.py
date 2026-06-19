"""
RAG pipeline: retrieve relevant chunks and generate cited answers.
"""

from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.services.embeddings import get_embedding_provider
from app.services.hybrid_search import hybrid_search
from app.services.llm import get_llm_provider

logger = get_logger("rag")


@dataclass
class Citation:
    """A source citation for a generated answer."""

    chunk_id: str
    document_id: str
    source: str
    index: int
    text: str
    score: float


@dataclass
class RAGAnswer:
    """Result of the RAG pipeline."""

    answer: str
    citations: List[Citation]
    provider: str


RAG_SYSTEM_PROMPT = """You are a precise document assistant. Answer the user's question using ONLY the provided context.
If the context does not contain enough information, say "I don't have enough information to answer that."
Do not make up facts. Include citations in your answer like [1], [2], etc."""


def _build_prompt(query: str, contexts: List[dict]) -> str:
    """Build a RAG prompt from query and retrieved contexts."""
    context_blocks = []
    for i, ctx in enumerate(contexts, start=1):
        source = ctx.get("source", "Unknown source")
        text = ctx.get("text", "").strip()
        context_blocks.append(f"[{i}] Source: {source}\n{text}")

    context_text = "\n\n".join(context_blocks)

    return f"""{RAG_SYSTEM_PROMPT}

Context:
{context_text}

Question: {query}

Answer:"""


async def answer_question(
    query: str,
    top_k: int = 5,
    document_id: Optional[str] = None,
    score_threshold: Optional[float] = 0.5,
    session: Optional[AsyncSession] = None,
    rerank: bool = True,
) -> RAGAnswer:
    """Run the full RAG pipeline.

    Args:
        query: User question.
        top_k: Number of chunks to retrieve.
        document_id: Optional document filter.
        score_threshold: Minimum vector similarity score.
        session: Optional database session for keyword/hybrid search.
        rerank: Whether to apply the configured reranker.

    Returns:
        RAGAnswer with generated text and citations.
    """
    logger.info("RAG query: %s", query)

    # 1. Retrieve relevant chunks via hybrid search (vector + keyword RRF)
    results = await hybrid_search(
        query=query,
        top_k=top_k,
        document_id=document_id,
        score_threshold=score_threshold,
        session=session,
        rerank=rerank,
    )

    logger.info("Retrieved %d chunks for query", len(results))

    if not results:
        return RAGAnswer(
            answer="I couldn't find any relevant information in the indexed documents.",
            citations=[],
            provider=get_embedding_provider().name,
        )

    # 2. Build citations
    citations = [
        Citation(
            chunk_id=r["id"],
            document_id=r["document_id"],
            source=r["source"],
            index=r["index"],
            text=r["text"],
            score=r["score"],
        )
        for r in results
    ]

    # 3. Generate answer with LLM
    llm_provider = get_llm_provider()
    prompt = _build_prompt(query, results)
    answer = await llm_provider.generate(
        prompt=prompt,
        system_message=RAG_SYSTEM_PROMPT,
        temperature=0.3,
    )

    return RAGAnswer(
        answer=answer,
        citations=citations,
        provider=llm_provider.name,
    )
