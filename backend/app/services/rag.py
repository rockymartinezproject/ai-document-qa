"""
RAG pipeline: retrieve relevant chunks, generate cited answers, and validate citations.
"""

import re
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.services.embeddings import get_embedding_provider
from app.services.hybrid_search import hybrid_search
from app.services.llm import get_llm_provider

logger = get_logger("rag")

_CITATION_RE = re.compile(r"\[(\d+)\]")


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
Do not make up facts. Cite your sources inline using [1], [2], etc., matching the numbered context chunks."""


def _build_prompt(query: str, contexts: List[dict]) -> str:
    """Build a RAG prompt from query and retrieved contexts."""
    context_blocks = []
    for i, ctx in enumerate(contexts, start=1):
        source = ctx.get("source", "Unknown source")
        index = ctx.get("index", 0)
        text = ctx.get("text", "").strip()
        context_blocks.append(f"[{i}] Source: {source} (chunk {index})\n{text}")

    context_text = "\n\n".join(context_blocks)

    return f"""{RAG_SYSTEM_PROMPT}

Context:
{context_text}

Question: {query}

Answer:"""


def _parse_and_renumber_citations(
    answer: str, contexts: List[dict]
) -> tuple[str, List[dict]]:
    """Validate citation markers, renumber them in answer order, and return cited contexts.

    Invalid markers (out of range) are replaced with [?]. If no valid markers are found,
    the original answer and all contexts are returned as a fallback.
    """
    if not contexts:
        return answer, []

    matches = list(_CITATION_RE.finditer(answer))
    original_to_new: dict[int, int] = {}
    next_num = 1

    for m in matches:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(contexts) and idx not in original_to_new:
            original_to_new[idx] = next_num
            next_num += 1

    if not original_to_new:
        # No valid citations found; keep original answer and all contexts.
        return answer, contexts

    def _replace_marker(m: re.Match) -> str:
        idx = int(m.group(1)) - 1
        new_num = original_to_new.get(idx)
        return f"[{new_num}]" if new_num is not None else "[?]"

    renumbered_answer = _CITATION_RE.sub(_replace_marker, answer)
    cited_contexts = [contexts[idx] for idx in original_to_new.keys()]
    return renumbered_answer, cited_contexts


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
        RAGAnswer with generated text and validated citations.
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

    # 2. Generate answer with LLM
    llm_provider = get_llm_provider()
    prompt = _build_prompt(query, results)
    answer = await llm_provider.generate(
        prompt=prompt,
        system_message=RAG_SYSTEM_PROMPT,
        temperature=0.3,
    )

    # 3. Validate and renumber citations, keeping only cited sources
    answer, cited_results = _parse_and_renumber_citations(answer, results)

    citations = [
        Citation(
            chunk_id=r["id"],
            document_id=r["document_id"],
            source=r["source"],
            index=r["index"],
            text=r["text"],
            score=r["score"],
        )
        for r in cited_results
    ]

    return RAGAnswer(
        answer=answer,
        citations=citations,
        provider=llm_provider.name,
    )


async def answer_question_stream(
    query: str,
    top_k: int = 5,
    document_id: Optional[str] = None,
    score_threshold: Optional[float] = 0.5,
    session: Optional[AsyncSession] = None,
    rerank: bool = True,
) -> AsyncIterator[Dict[str, Any]]:
    """Stream the RAG pipeline as a series of events.

    Events:
        {"type": "citations", "citations": [...]}
        {"type": "token", "token": "..."}
        {"type": "done", "answer": "...", "citations": [...], "provider": "..."}

    Args:
        query: User question.
        top_k: Number of chunks to retrieve.
        document_id: Optional document filter.
        score_threshold: Minimum vector similarity score.
        session: Optional database session for keyword/hybrid search.
        rerank: Whether to apply the configured reranker.
    """
    logger.info("Streaming RAG query: %s", query)

    results = await hybrid_search(
        query=query,
        top_k=top_k,
        document_id=document_id,
        score_threshold=score_threshold,
        session=session,
        rerank=rerank,
    )

    logger.info("Retrieved %d chunks for streaming query", len(results))

    if not results:
        yield {
            "type": "done",
            "answer": "I couldn't find any relevant information in the indexed documents.",
            "citations": [],
            "provider": get_embedding_provider().name,
        }
        return

    all_citations = [
        {
            "chunk_id": r["id"],
            "document_id": r["document_id"],
            "source": r["source"],
            "index": r["index"],
            "text": r["text"],
            "score": r["score"],
        }
        for r in results
    ]
    yield {"type": "citations", "citations": all_citations}

    llm_provider = get_llm_provider()
    prompt = _build_prompt(query, results)
    answer_parts: List[str] = []

    async for token in llm_provider.generate_stream(
        prompt=prompt,
        system_message=RAG_SYSTEM_PROMPT,
        temperature=0.3,
    ):
        answer_parts.append(token)
        yield {"type": "token", "token": token}

    answer = "".join(answer_parts)
    answer, cited_results = _parse_and_renumber_citations(answer, results)

    final_citations = [
        Citation(
            chunk_id=r["id"],
            document_id=r["document_id"],
            source=r["source"],
            index=r["index"],
            text=r["text"],
            score=r["score"],
        )
        for r in cited_results
    ]

    yield {
        "type": "done",
        "answer": answer,
        "citations": final_citations,
        "provider": llm_provider.name,
    }
