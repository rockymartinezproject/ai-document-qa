"""Tests for the chunking strategies."""

import pytest

from app.services.chunking import chunk_document_async


@pytest.fixture
def sample_text():
    return "\n\n".join(f"Paragraph {i}: " + "word " * 50 for i in range(10))


async def test_recursive_chunking(sample_text):
    chunks = await chunk_document_async(
        text=sample_text,
        document_id="doc-1",
        source="test.txt",
        strategy="recursive",
        chunk_size=200,
        chunk_overlap=50,
    )

    assert len(chunks) > 0
    assert all(c.document_id == "doc-1" for c in chunks)
    assert all(c.text for c in chunks)

    # Chunks should be ordered and cover the text progressively
    for prev, curr in zip(chunks, chunks[1:]):
        assert curr.start_char >= prev.start_char
        assert curr.end_char > prev.end_char


async def test_hierarchical_chunking(sample_text):
    chunks = await chunk_document_async(
        text=sample_text,
        document_id="doc-1",
        source="test.txt",
        strategy="hierarchical",
        chunk_size=400,
        chunk_overlap=100,
    )

    assert len(chunks) > 0
    parents = [c for c in chunks if c.level == 0]
    children = [c for c in chunks if c.level > 0]
    assert len(parents) > 0
    for child in children:
        assert child.parent_chunk_id is not None


async def test_empty_text():
    chunks = await chunk_document_async(
        text="",
        document_id="doc-empty",
        source="empty.txt",
    )
    assert chunks == []
