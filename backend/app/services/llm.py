"""
LLM provider abstraction: OpenAI, Anthropic, Ollama, and mock fallback.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("llm")


class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    name: str = "unknown"

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """Generate text from a prompt.

        Args:
            prompt: The full prompt text.
            system_message: Optional system instructions.
            temperature: Sampling temperature.

        Returns:
            Generated text response.
        """
        ...


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    name = "openai"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        import openai

        self._client = openai.AsyncOpenAI(api_key=api_key or settings.OPENAI_API_KEY)
        self._model = model or settings.DEFAULT_LLM_MODEL

    async def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        logger.info("Calling OpenAI model=%s", self._model)
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    name = "anthropic"

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        import anthropic

        self._client = anthropic.AsyncAnthropic(api_key=api_key or settings.ANTHROPIC_API_KEY)
        self._model = model

    async def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        logger.info("Calling Anthropic model=%s", self._model)
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            temperature=temperature,
            system=system_message or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text if response.content else ""


class OllamaProvider(LLMProvider):
    """Local LLM via Ollama."""

    name = "ollama"

    def __init__(self, base_url: Optional[str] = None, model: str = "llama3.2"):
        self._base_url = base_url or settings.LOCAL_LLM_URL
        self._model = model

    async def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        logger.info("Calling Ollama model=%s at %s", self._model, self._base_url)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "system": system_message or "You are a helpful assistant.",
                    "stream": False,
                    "options": {"temperature": temperature},
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")


class MockProvider(LLMProvider):
    """Mock provider for testing without API keys.

    Returns a simple answer based on the prompt context.
    """

    name = "mock"

    async def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        logger.info("Using mock LLM provider")

        # Extract context from the RAG prompt
        if "Context:" in prompt and "Question:" in prompt:
            context = prompt.split("Context:")[1].split("Question:")[0].strip()
            question = prompt.split("Question:")[1].split("Answer:")[0].strip()

            # Simple heuristic answer
            return (
                f"[Mock LLM] Based on the retrieved context, here's what I found "
                f"regarding your question: '{question}'\n\n"
                f"The relevant context includes:\n{context[:500]}...\n\n"
                f"(Set OPENAI_API_KEY or ANTHROPIC_API_KEY to get real LLM responses.)"
            )

        return "[Mock LLM] This is a placeholder response. Configure an LLM API key for real answers."


# Singleton provider instance
_provider: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """Return the best available LLM provider.

    Priority: OpenAI > Anthropic > Ollama > Mock
    """
    global _provider

    if _provider is not None:
        return _provider

    if settings.OPENAI_API_KEY:
        logger.info("Using OpenAI LLM provider")
        _provider = OpenAIProvider()
    elif settings.ANTHROPIC_API_KEY:
        logger.info("Using Anthropic LLM provider")
        _provider = AnthropicProvider()
    elif settings.LOCAL_LLM_URL:
        logger.info("Using Ollama LLM provider")
        _provider = OllamaProvider()
    else:
        logger.warning("No LLM API key configured, using mock provider")
        _provider = MockProvider()

    return _provider


def clear_llm_provider() -> None:
    """Clear cached LLM provider (useful for testing)."""
    global _provider
    _provider = None
