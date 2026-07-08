"""Tests for the authentication endpoints."""

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _unique_email():
    return f"user_{uuid.uuid4().hex[:8]}@example.com"


def test_register_and_login():
    with TestClient(app) as client:
        email = _unique_email()
        password = "secret123"

        # Register
        register_res = client.post(
            "/api/auth/register", json={"email": email, "password": password}
        )
        assert register_res.status_code == 201
        register_data = register_res.json()
        assert register_data["success"] is True
        assert register_data["data"]["email"] == email

        # Login
        login_res = client.post(
            "/api/auth/login", json={"email": email, "password": password}
        )
        assert login_res.status_code == 200
        login_data = login_res.json()
        assert login_res.json()["success"] is True
        token = login_data["data"]["access_token"]
        assert token
        assert login_data["data"]["user"]["email"] == email

        # Me
        me_res = client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_res.status_code == 200
        assert me_res.json()["data"]["email"] == email


def test_protected_route_without_token():
    with TestClient(app) as client:
        response = client.get("/api/documents")
        assert response.status_code == 401
