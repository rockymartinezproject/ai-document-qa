"""Tests for keyword search over chunks."""

import pytest

from app.db.models import Chunk, Document
from app.services.keyword_search import search_chunks_keywords


@pytest.fixture
async def sample_document(db_session):
    document = Document(
        id="doc-keyword",
        user_id=None,
        filename="test.pdf",
        content_type="application/pdf",
        file_path="/tmp/test.pdf",
        file_size=100,
        extracted_text="alpha beta gamma delta",
        status="indexed",
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    chunks = [
        Chunk(
            id="chunk-1",
            document_id=document.id,
            index=0,
            text="The quick brown fox jumps over the lazy dog.",
            source="test.pdf",
            start_char=0,
            end_char=44,
        ),
        Chunk(
            id="chunk-2",
            document_id=document.id,
            index=1,
            text="Machine learning is transforming software engineering.",
            source="test.pdf",
            start_char=45,
            end_char=99,
        ),
    ]
    for chunk in chunks:
        db_session.add(chunk)
    await db_session.commit()
    return document


async def test_keyword_search_finds_matching_chunks(db_session, sample_document):
    results = await search_chunks_keywords(db_session, "machine learning", top_k=5)
    assert len(results) == 1
    assert results[0]["id"] == "chunk-2"


async def test_keyword_search_respects_document_filter(db_session, sample_document):
    results = await search_chunks_keywords(
        db_session, "quick fox", top_k=5, document_id=sample_document.id
    )
    assert len(results) == 1
    assert results[0]["id"] == "chunk-1"


async def test_keyword_search_no_matches(db_session, sample_document):
    results = await search_chunks_keywords(db_session, "nonexistent term", top_k=5)
    assert results == []
