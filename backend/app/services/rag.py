"""
RAG pipeline: retrieve relevant chunks and generate cited answers.
"""

from dataclasses import dataclass
from typing import List, Optional

from app.core.logging import get_logger
from app.services.embeddings import get_embedding_provider
from app.services.llm import get_llm_provider
from app.services.vector_store import search_similar

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
) -> RAGAnswer:
    """Run the full RAG pipeline.

    Args:
        query: User question.
        top_k: Number of chunks to retrieve.
        document_id: Optional document filter.
        score_threshold: Minimum similarity score.

    Returns:
        RAGAnswer with generated text and citations.
    """
    logger.info("RAG query: %s", query)

    # 1. Embed query
    embedding_provider = get_embedding_provider()
    query_vectors = await embedding_provider.embed([query])

    if not query_vectors or not query_vectors[0]:
        raise RuntimeError("Failed to embed query")

    # 2. Retrieve relevant chunks
    results = await search_similar(
        query_vector=query_vectors[0],
        top_k=top_k,
        document_id=document_id,
        score_threshold=score_threshold,
    )

    logger.info("Retrieved %d chunks for query", len(results))

    if not results:
        return RAGAnswer(
            answer="I couldn't find any relevant information in the indexed documents.",
            citations=[],
            provider=embedding_provider.name,
        )

    # 3. Build citations
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

    # 4. Generate answer with LLM
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
