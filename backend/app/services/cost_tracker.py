"""
Cost tracking: token counting and price estimation for LLM usage.
"""

from typing import Dict

from app.core.logging import get_logger

logger = get_logger("cost_tracker")

# Prices per 1,000 tokens (input / output).
# Approximate values for supported models; update as provider pricing changes.
MODEL_PRICES: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "mock": {"input": 0.0, "output": 0.0},
    "ollama": {"input": 0.0, "output": 0.0},
}

# Optional tiktoken import; if unavailable (e.g. Python 3.14 without wheels),
# we fall back to a simple approximation.
try:
    import tiktoken

    _tiktoken_available = True
except Exception:
    _tiktoken_available = False
    tiktoken = None  # type: ignore


def _get_encoder(model: str):
    """Return a tiktoken encoder for the model, falling back to cl100k_base."""
    if not _tiktoken_available or tiktoken is None:
        return None
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        pass
    except Exception:
        # Network/cache errors when fetching model-specific encodings.
        logger.warning("Failed to load tiktoken encoder for %s", model, exc_info=True)

    # Fallback to a commonly cached encoding; ignore errors so we can approximate.
    try:
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        logger.warning("Failed to load cl100k_base tiktoken encoder")
        return None


def _approximate_tokens(text: str) -> int:
    """Fallback token count: ~4 characters per token on average."""
    return max(1, len(text) // 4) if text else 0


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens in text for the given model.

    Falls back to a simple approximation if tiktoken is unavailable.
    """
    if not text:
        return 0

    encoder = _get_encoder(model)
    if encoder is None:
        return _approximate_tokens(text)

    try:
        return len(encoder.encode(text))
    except Exception as e:
        logger.warning("Token counting failed: %s. Falling back.", e)
        return _approximate_tokens(text)


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gpt-4o",
) -> float:
    """Estimate cost in USD for a request.

    Returns 0.0 for unknown local/mock providers.
    """
    prices = MODEL_PRICES.get(model.lower())
    if not prices:
        # Try common prefix matching
        for key, value in MODEL_PRICES.items():
            if model.lower().startswith(key.lower()):
                prices = value
                break
        if not prices:
            logger.warning("No pricing for model %s; treating as free", model)
            return 0.0

    input_cost = input_tokens * (prices["input"] / 1000)
    output_cost = output_tokens * (prices["output"] / 1000)
    return round(input_cost + output_cost, 6)
