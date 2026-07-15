"""Tests for slowapi rate limiting integration."""

import pytest

from app.core.limiter import limiter


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Clear the in-memory rate limiter before each test."""
    limiter.reset()
    yield


def _register(client, email: str):
    return client.post(
        "/api/auth/register",
        json={"email": email, "password": "TestPass123!"},
    )


def test_register_rate_limit(client):
    """The /api/auth/register endpoint enforces 5 requests per minute."""
    for i in range(5):
        response = _register(client, f"rate-limit-{i}@example.com")
        assert response.status_code == 201, response.text

    response = _register(client, "rate-limit-blocked@example.com")
    assert response.status_code == 429
