"""Integration tests for document upload and management endpoints."""

from io import BytesIO

import pytest
from pypdf import PdfWriter

from tests.conftest import create_test_user, user_token


def _pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(612, 792)
    buffer = BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
async def auth_user(db_session):
    user = create_test_user(db_session, "docs-test@example.com", "password123")
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def test_upload_pdf(client, auth_user, upload_dir):
    token = user_token(auth_user)
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", _pdf_bytes(), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["filename"] == "test.pdf"


async def test_list_documents_is_user_scoped(client, auth_user, upload_dir):
    token = user_token(auth_user)

    # Upload one document
    client.post(
        "/api/documents/upload",
        files={"file": ("list-test.pdf", _pdf_bytes(), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get("/api/documents", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    docs = response.json()["data"]
    assert len(docs) == 1
    assert docs[0]["filename"] == "list-test.pdf"


async def test_delete_document(client, auth_user, upload_dir):
    token = user_token(auth_user)

    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("delete-test.pdf", _pdf_bytes(), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    doc_id = upload_res.json()["data"]["id"]

    delete_res = client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_res.status_code == 200

    list_res = client.get("/api/documents", headers={"Authorization": f"Bearer {token}"})
    assert len(list_res.json()["data"]) == 0


async def test_cannot_access_other_users_document(client, db_session, upload_dir):
    owner = create_test_user(db_session, "owner@example.com", "password123")
    other = create_test_user(db_session, "other@example.com", "password123")
    await db_session.commit()
    await db_session.refresh(owner)
    await db_session.refresh(other)

    owner_token = user_token(owner)
    other_token = user_token(other)

    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("private.pdf", _pdf_bytes(), "application/pdf")},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    doc_id = upload_res.json()["data"]["id"]

    # Other user cannot see it in their list
    list_res = client.get("/api/documents", headers={"Authorization": f"Bearer {other_token}"})
    assert len(list_res.json()["data"]) == 0

    # Other user cannot delete it
    delete_res = client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert delete_res.status_code == 404
