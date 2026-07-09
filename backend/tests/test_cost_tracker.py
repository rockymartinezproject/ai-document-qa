"""Tests for the cost tracker utilities."""

from app.services.cost_tracker import count_tokens, estimate_cost


def test_count_tokens_returns_non_negative():
    assert count_tokens("hello world", "gpt-4o") >= 0
    assert count_tokens("", "gpt-4o") == 0


def test_estimate_cost_returns_zero_for_zero_tokens():
    assert estimate_cost(0, 0, "gpt-4o") == 0.0


def test_estimate_cost_known_model():
    # gpt-4o: $2.5 / 1M input, $10 / 1M output
    cost = estimate_cost(1_000_000, 1_000_000, "gpt-4o")
    assert cost == 12.5


def test_estimate_cost_unknown_model():
    cost = estimate_cost(1_000_000, 0, "unknown-model")
    assert cost >= 0.0
