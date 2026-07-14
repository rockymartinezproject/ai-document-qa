"""Integration tests for conversation endpoints."""

import pytest

from tests.conftest import create_test_user, user_token


@pytest.fixture
async def auth_user(db_session):
    user = create_test_user(db_session, "conv-test@example.com", "password123")
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def test_create_and_list_conversations(client, auth_user):
    token = user_token(auth_user)

    create_res = client.post(
        "/api/conversations",
        json={"title": "My conversation"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_res.status_code == 200
    conv = create_res.json()["data"]
    assert conv["title"] == "My conversation"

    list_res = client.get("/api/conversations", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) == 1


async def test_get_conversation(client, auth_user):
    token = user_token(auth_user)

    create_res = client.post(
        "/api/conversations",
        json={"title": "Fetch me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    conv_id = create_res.json()["data"]["id"]

    get_res = client.get(
        f"/api/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == conv_id


async def test_rename_conversation(client, auth_user):
    token = user_token(auth_user)

    create_res = client.post(
        "/api/conversations",
        json={"title": "Old title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    conv_id = create_res.json()["data"]["id"]

    put_res = client.put(
        f"/api/conversations/{conv_id}",
        json={"title": "New title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_res.status_code == 200
    assert put_res.json()["data"]["title"] == "New title"


async def test_delete_conversation(client, auth_user):
    token = user_token(auth_user)

    create_res = client.post(
        "/api/conversations",
        json={"title": "To delete"},
        headers={"Authorization": f"Bearer {token}"},
    )
    conv_id = create_res.json()["data"]["id"]

    del_res = client.delete(
        f"/api/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 200

    get_res = client.get(
        f"/api/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 404


async def test_conversation_isolation(client, db_session):
    owner = create_test_user(db_session, "conv-owner@example.com", "password123")
    other = create_test_user(db_session, "conv-other@example.com", "password123")
    await db_session.commit()
    await db_session.refresh(owner)
    await db_session.refresh(other)

    owner_token = user_token(owner)
    other_token = user_token(other)

    create_res = client.post(
        "/api/conversations",
        json={"title": "Private"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    conv_id = create_res.json()["data"]["id"]

    other_get = client.get(
        f"/api/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_get.status_code == 404
