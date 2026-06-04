"""
Dependency injection providers for FastAPI.

Usage:
    @router.get("/items")
    async def get_items(settings: Settings = Depends(get_settings)):
        ...
"""

from functools import lru_cache

from app.core.config import Settings, settings
from app.core.logging import get_logger

logger = get_logger("deps")


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings.

    Using lru_cache ensures we don't reload .env on every request.
    """
    return settings


def get_logger_instance(name: str = "api"):
    """Return a logger instance."""
    return get_logger(name)
