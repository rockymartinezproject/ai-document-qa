"""
RAG evaluation metrics and dataset/run helpers.

Implements a lightweight, dependency-free evaluation pipeline using:
- context_precision: token overlap between retrieved and expected contexts
- answer_relevance: embedding cosine similarity between query and answer
- faithfulness: token overlap between answer and retrieved contexts
"""

import math
import re
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import Chunk
from app.services.embeddings import get_embedding_provider
from app.services.llm import create_llm_provider, get_llm_provider

logger = get_logger("evaluation")


def _tokens(text: str) -> set[str]:
    """Return a set of normalized alphanumeric tokens."""
    return set(re.findall(r"\b[a-z0-9]+\b", text.lower()))


def _token_overlap(a: str, b: str) -> float:
    """Jaccard-ish overlap ratio of token sets (intersection / max len)."""
    tokens_a = _tokens(a)
    tokens_b = _tokens(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    return intersection / max(len(tokens_a), len(tokens_b))


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _context_precision(
    retrieved_contexts: List[str],
    expected_contexts: List[str],
) -> float:
    """Measure how much of the retrieved context overlaps expected context."""
    if not retrieved_contexts or not expected_contexts:
        return 0.0

    expected_text = " ".join(expected_contexts)
    scores = [_token_overlap(ctx, expected_text) for ctx in retrieved_contexts]
    return sum(scores) / len(scores)


def _faithfulness(answer: str, retrieved_contexts: List[str]) -> float:
    """Measure how well the answer is grounded in retrieved contexts."""
    if not answer or not retrieved_contexts:
        return 0.0

    context_text = " ".join(retrieved_contexts)
    return _token_overlap(answer, context_text)


async def _answer_relevance(query: str, answer: str) -> float:
    """Measure semantic similarity between the query and generated answer."""
    if not query or not answer:
        return 0.0

    provider = get_embedding_provider()
    embeddings = await provider.embed([query, answer])
    if len(embeddings) < 2:
        return 0.0

    return max(0.0, _cosine_similarity(embeddings[0], embeddings[1]))


def _overall(metrics: Dict[str, float]) -> float:
    """Average of the three metrics."""
    return round(sum(metrics.values()) / 3, 4)


async def evaluate_sample(
    query: str,
    expected_answer: str,
    contexts: List[str],
    actual_answer: str,
    retrieved_contexts: List[str],
) -> Dict[str, float]:
    """Compute evaluation metrics for a single RAG sample."""
    context_precision = _context_precision(retrieved_contexts, contexts)
    faithfulness = _faithfulness(actual_answer, retrieved_contexts)
    relevance = await _answer_relevance(query, actual_answer)

    metrics = {
        "context_precision": round(context_precision, 4),
        "answer_relevance": round(relevance, 4),
        "faithfulness": round(faithfulness, 4),
    }
    metrics["overall"] = _overall(metrics)
    return metrics


def aggregate_metrics(results: List[Dict[str, float]]) -> Dict[str, float]:
    """Average each metric across a list of per-sample metric dicts."""
    if not results:
        return {
            "context_precision": 0.0,
            "answer_relevance": 0.0,
            "faithfulness": 0.0,
            "overall": 0.0,
        }

    keys = ["context_precision", "answer_relevance", "faithfulness", "overall"]
    return {key: round(sum(r[key] for r in results) / len(results), 4) for key in keys}


def has_regression(current_overall: float, previous_overall: Optional[float], threshold: float = 0.05) -> bool:
    """Return True if the current score dropped more than threshold vs the previous run."""
    if previous_overall is None:
        return False
    return (previous_overall - current_overall) > threshold


async def generate_dataset(
    session: AsyncSession,
    document_id: str,
    sample_count: int = 3,
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Generate synthetic Q&A pairs from a document's chunks."""
    result = await session.execute(
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .order_by(Chunk.index)
        .limit(sample_count * 2)
    )
    chunks = result.scalars().all()
    if not chunks:
        return []

    # Prefer leaf-level chunks (children in hierarchical, all in recursive/semantic)
    leaf_chunks = [c for c in chunks if c.level == 1] or list(chunks)
    selected = leaf_chunks[:sample_count]

    provider = (
        create_llm_provider(provider_name, model)
        if provider_name
        else get_llm_provider()
    )

    samples = []
    for chunk in selected:
        prompt = (
            "Generate a concise question and a short answer based ONLY on the following context.\n"
            "Format your response exactly as:\n"
            "Question: <question>\n"
            "Answer: <answer>\n\n"
            f"Context:\n{chunk.text[:1000]}"
        )
        try:
            output = await provider.generate(
                prompt=prompt,
                system_message="You are a helpful assistant that creates reading-comprehension questions.",
                temperature=0.3,
            )
        except Exception as exc:
            logger.warning("Failed to generate sample for chunk %s: %s", chunk.id, exc)
            continue

        question = ""
        answer = ""
        for line in output.splitlines():
            if line.lower().startswith("question:"):
                question = line.split(":", 1)[1].strip()
            elif line.lower().startswith("answer:"):
                answer = line.split(":", 1)[1].strip()

        if question and answer:
            samples.append(
                {
                    "query": question,
                    "expected_answer": answer,
                    "context": chunk.text,
                    "chunk_id": chunk.id,
                }
            )

    return samples


def format_evaluation_report(
    results: List[Dict[str, Any]], aggregate: Dict[str, float]
) -> str:
    """Return a human-readable summary of an evaluation run."""
    lines = ["Evaluation Report", "=" * 40]
    lines.append(f"Samples: {len(results)}")
    lines.append(
        f"Overall: {aggregate['overall']:.2f} "
        f"(precision={aggregate['context_precision']:.2f}, "
        f"relevance={aggregate['answer_relevance']:.2f}, "
        f"faithfulness={aggregate['faithfulness']:.2f})"
    )
    return "\n".join(lines)
