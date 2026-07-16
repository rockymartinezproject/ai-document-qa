"""Tests for admin-only user management endpoints."""

import pytest

from tests.conftest import create_test_user, user_token


@pytest.fixture
async def admin_user(db_session):
    user = create_test_user(
        db_session, "admin@example.com", "admin-password", is_superuser=True
    )
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def normal_user(db_session):
    user = create_test_user(db_session, "normal@example.com", "normal-password")
    await db_session.commit()
    await db_session.refresh(user)
    return user


def _auth_header(user):
    return {"Authorization": f"Bearer {user_token(user)}"}


def test_list_users_requires_admin(client, normal_user):
    response = client.get("/api/admin/users", headers=_auth_header(normal_user))
    assert response.status_code == 403


def test_list_users_returns_all_users(client, admin_user, normal_user):
    response = client.get("/api/admin/users", headers=_auth_header(admin_user))
    assert response.status_code == 200

    data = response.json()["data"]
    emails = {user["email"] for user in data}
    assert admin_user.email in emails
    assert normal_user.email in emails

    admin_data = next(user for user in data if user["email"] == admin_user.email)
    assert admin_data["is_superuser"] is True


def test_update_user_status(client, admin_user, normal_user):
    response = client.patch(
        f"/api/admin/users/{normal_user.id}",
        json={"is_superuser": True},
        headers=_auth_header(admin_user),
    )
    assert response.status_code == 200
    assert response.json()["data"]["is_superuser"] is True


def test_admin_cannot_deactivate_self(client, admin_user):
    response = client.patch(
        f"/api/admin/users/{admin_user.id}",
        json={"is_active": False},
        headers=_auth_header(admin_user),
    )
    assert response.status_code == 400
