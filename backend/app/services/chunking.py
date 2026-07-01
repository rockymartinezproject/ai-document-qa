"""
Text chunking strategies: recursive, semantic, and hierarchical.
"""

import math
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("chunking")

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

# Sentence boundary regex: keep delimiters attached to preceding sentence.
_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]+|\s*[^.!?]+$", re.UNICODE)


@dataclass
class Chunk:
    """A single text chunk with metadata."""

    text: str
    index: int
    document_id: str
    source: str
    start_char: int
    end_char: int
    id: Optional[str] = None
    parent_chunk_id: Optional[str] = None
    level: int = 0
    strategy: str = "recursive"
    metadata: Dict[str, Any] = field(default_factory=dict)


def _split_text(text: str, separator: str) -> List[str]:
    """Split text by a separator, keeping the separator if it's meaningful."""
    if separator == "":
        return list(text)
    parts = text.split(separator)
    result = []
    for i, part in enumerate(parts):
        if i < len(parts) - 1:
            result.append(part + separator)
        else:
            result.append(part)
    return [r for r in result if r]


def _merge_splits(
    splits: List[str],
    separator: str,
    chunk_size: int,
    chunk_overlap: int,
) -> List[str]:
    """Merge small splits into chunks of appropriate size with overlap."""
    chunks = []
    current_chunk = []
    current_length = 0

    for split in splits:
        split_length = len(split)

        if split_length > chunk_size:
            if current_chunk:
                chunks.append("".join(current_chunk).strip())
            chunks.append(split.strip())
            current_chunk = []
            current_length = 0
            continue

        if current_length + split_length > chunk_size and current_chunk:
            chunks.append("".join(current_chunk).strip())
            overlap_splits = []
            overlap_length = 0
            for s in reversed(current_chunk):
                if overlap_length + len(s) <= chunk_overlap:
                    overlap_splits.insert(0, s)
                    overlap_length += len(s)
                else:
                    break
            current_chunk = overlap_splits
            current_length = overlap_length

        current_chunk.append(split)
        current_length += split_length

    if current_chunk:
        final = "".join(current_chunk).strip()
        if final:
            chunks.append(final)

    return chunks


def recursive_split(
    text: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    separators: Optional[List[str]] = None,
) -> List[str]:
    """Recursively split text into chunks using a hierarchy of separators."""
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    separators = separators or DEFAULT_SEPARATORS

    if not text or not text.strip():
        return []

    final_chunks = []

    def _recurse(remaining_text: str, separator_idx: int):
        if separator_idx >= len(separators):
            for i in range(0, len(remaining_text), chunk_size):
                final_chunks.append(remaining_text[i : i + chunk_size])
            return

        separator = separators[separator_idx]
        splits = _split_text(remaining_text, separator)

        if all(len(s) <= chunk_size for s in splits):
            merged = _merge_splits(splits, separator, chunk_size, chunk_overlap)
            final_chunks.extend(merged)
            return

        buffer = []
        buffer_len = 0
        for split in splits:
            if len(split) > chunk_size:
                if buffer:
                    merged = _merge_splits(buffer, separator, chunk_size, chunk_overlap)
                    final_chunks.extend(merged)
                    buffer = []
                    buffer_len = 0
                _recurse(split, separator_idx + 1)
            else:
                buffer.append(split)
                buffer_len += len(split)

        if buffer:
            merged = _merge_splits(buffer, separator, chunk_size, chunk_overlap)
            final_chunks.extend(merged)

    _recurse(text.strip(), 0)

    seen = set()
    result = []
    for chunk in final_chunks:
        key = chunk.strip()
        if key and key not in seen:
            seen.add(key)
            result.append(key)

    return result


def _sentence_spans(text: str) -> List[tuple[str, int, int]]:
    """Return (sentence, start_char, end_char) for each sentence in text."""
    spans = []
    for match in _SENTENCE_RE.finditer(text):
        sentence = match.group(0).strip()
        if sentence:
            spans.append((sentence, match.start(), match.end()))
    return spans


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def semantic_split(
    text: str,
    max_chunk_size: Optional[int] = None,
    similarity_threshold: Optional[float] = None,
) -> List[tuple[str, int, int, Dict[str, Any]]]:
    """Split text into semantic chunks based on sentence embedding similarity.

    Returns a list of (chunk_text, start_char, end_char, metadata).
    """
    max_chunk_size = max_chunk_size or settings.SEMANTIC_MAX_CHUNK_SIZE
    similarity_threshold = similarity_threshold or settings.SEMANTIC_SIMILARITY_THRESHOLD

    spans = _sentence_spans(text)
    if not spans:
        return []

    if len(spans) == 1:
        sentence, start, end = spans[0]
        return [(sentence, start, end, {"sentence_count": 1, "sentence_indices": [0]})]

    from app.services.embeddings import get_embedding_provider

    provider = get_embedding_provider()
    sentences = [s for s, _, _ in spans]
    embeddings = await provider.embed(sentences)

    chunks: List[tuple[str, int, int, Dict[str, Any]]] = []
    group_sentences: List[int] = [0]
    group_embeddings: List[List[float]] = [embeddings[0]]
    group_start = spans[0][1]
    group_end = spans[0][2]

    def _avg_embedding(indices: List[int]) -> List[float]:
        vecs = [embeddings[i] for i in indices]
        dim = len(vecs[0])
        return [sum(v[i] for v in vecs) / len(vecs) for i in range(dim)]

    def _flush():
        nonlocal group_sentences, group_embeddings, group_start, group_end
        if not group_sentences:
            return
        text_parts = [spans[i][0] for i in group_sentences]
        chunk_text = " ".join(text_parts)
        metadata = {
            "sentence_count": len(group_sentences),
            "sentence_indices": list(group_sentences),
        }
        chunks.append((chunk_text, group_start, group_end, metadata))
        group_sentences = []
        group_embeddings = []

    for i in range(1, len(spans)):
        sentence, start, end = spans[i]
        candidate_len = end - group_start

        if candidate_len > max_chunk_size and group_sentences:
            _flush()
            group_sentences = [i]
            group_embeddings = [embeddings[i]]
            group_start = start
            group_end = end
            continue

        avg = _avg_embedding(group_sentences)
        sim = _cosine_similarity(avg, embeddings[i])

        if sim >= similarity_threshold:
            group_sentences.append(i)
            group_embeddings.append(embeddings[i])
            group_end = end
        else:
            _flush()
            group_sentences = [i]
            group_embeddings = [embeddings[i]]
            group_start = start
            group_end = end

    _flush()
    return chunks


def hierarchical_split(
    text: str,
    parent_size: Optional[int] = None,
    child_size: Optional[int] = None,
    child_overlap: Optional[int] = None,
) -> List[Chunk]:
    """Create hierarchical parent/child chunks.

    Returns parent chunks (level=0) followed by their child chunks (level=1).
    Child chunks reference their parent via parent_chunk_id.
    """
    parent_size = parent_size or settings.HIERARCHICAL_PARENT_SIZE
    child_size = child_size or settings.HIERARCHICAL_CHILD_SIZE
    child_overlap = child_overlap or settings.HIERARCHICAL_OVERLAP

    if not text or not text.strip():
        return []

    parent_texts = recursive_split(text, chunk_size=parent_size, chunk_overlap=child_overlap)
    all_chunks: List[Chunk] = []
    parent_index = 0
    child_index = 0
    cursor = 0

    for p_text in parent_texts:
        parent_id = str(uuid.uuid4())
        p_start = text.find(p_text, cursor)
        if p_start == -1:
            p_start = cursor
        p_end = p_start + len(p_text)
        cursor = max(cursor, p_end - child_overlap)

        parent_chunk = Chunk(
            text=p_text,
            index=parent_index,
            document_id="",
            source="",
            start_char=p_start,
            end_char=p_end,
            id=parent_id,
            level=0,
            strategy="hierarchical",
            metadata={"type": "parent"},
        )
        all_chunks.append(parent_chunk)
        parent_index += 1

        child_texts = recursive_split(p_text, chunk_size=child_size, chunk_overlap=child_overlap)
        child_cursor = 0
        for c_text in child_texts:
            c_start = p_text.find(c_text, child_cursor)
            if c_start == -1:
                c_start = child_cursor
            c_end = c_start + len(c_text)
            child_cursor = max(child_cursor, c_end - child_overlap)

            all_chunks.append(
                Chunk(
                    text=c_text,
                    index=child_index,
                    document_id="",
                    source="",
                    start_char=p_start + c_start,
                    end_char=p_start + c_end,
                    parent_chunk_id=parent_id,
                    level=1,
                    strategy="hierarchical",
                    metadata={"type": "child", "parent_index": parent_index - 1},
                )
            )
            child_index += 1

    return all_chunks


def _build_recursive_chunks(
    text: str,
    document_id: str,
    source: str,
    chunk_size: Optional[int],
    chunk_overlap: Optional[int],
) -> List[Chunk]:
    texts = recursive_split(text, chunk_size, chunk_overlap)
    chunks = []
    cursor = 0
    overlap = chunk_overlap or settings.CHUNK_OVERLAP

    for i, chunk_text in enumerate(texts):
        start = text.find(chunk_text, cursor)
        if start == -1:
            start = cursor
        end = start + len(chunk_text)
        cursor = max(cursor, end - overlap)

        chunks.append(
            Chunk(
                text=chunk_text,
                index=i,
                document_id=document_id,
                source=source,
                start_char=start,
                end_char=end,
                level=0,
                strategy="recursive",
            )
        )

    return chunks


async def _build_semantic_chunks(
    text: str,
    document_id: str,
    source: str,
) -> List[Chunk]:
    split = await semantic_split(text)
    chunks = []
    for i, (chunk_text, start, end, metadata) in enumerate(split):
        chunks.append(
            Chunk(
                text=chunk_text,
                index=i,
                document_id=document_id,
                source=source,
                start_char=start,
                end_char=end,
                level=0,
                strategy="semantic",
                metadata=metadata,
            )
        )
    return chunks


def _build_hierarchical_chunks(
    text: str,
    document_id: str,
    source: str,
) -> List[Chunk]:
    chunks = hierarchical_split(text)
    for chunk in chunks:
        chunk.document_id = document_id
        chunk.source = source
    return chunks


def chunk_document(
    text: str,
    document_id: str,
    source: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    strategy: Optional[str] = None,
) -> List[Chunk]:
    """Split document text into Chunk objects using the configured strategy.

    Args:
        text: Full extracted text.
        document_id: Parent document UUID.
        source: Human-readable source identifier (filename or URL).
        chunk_size: Target chunk size (recursive only).
        chunk_overlap: Overlap size (recursive only).
        strategy: Chunking strategy. Defaults to settings.CHUNK_STRATEGY.

    Returns:
        List of Chunk dataclasses.
    """
    strategy = (strategy or settings.CHUNK_STRATEGY).lower().strip()

    if strategy == "semantic":
        # semantic_split is async because it needs embeddings
        raise RuntimeError(
            "Use chunk_document_async() for semantic chunking or call from an async context."
        )

    if strategy == "hierarchical":
        return _build_hierarchical_chunks(text, document_id, source)

    return _build_recursive_chunks(
        text, document_id, source, chunk_size, chunk_overlap
    )


async def chunk_document_async(
    text: str,
    document_id: str,
    source: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    strategy: Optional[str] = None,
) -> List[Chunk]:
    """Async version of chunk_document; required for semantic chunking."""
    strategy = (strategy or settings.CHUNK_STRATEGY).lower().strip()

    if strategy == "semantic":
        return await _build_semantic_chunks(text, document_id, source)

    if strategy == "hierarchical":
        return _build_hierarchical_chunks(text, document_id, source)

    return _build_recursive_chunks(
        text, document_id, source, chunk_size, chunk_overlap
    )
