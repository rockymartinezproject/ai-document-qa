"""Dependency injection providers for FastAPI.

Usage:
    @router.get("/items")
    async def get_items(settings: Settings = Depends(get_settings)):
        ...
"""

from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, settings
from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.db.base import get_db
from app.db.models import User

logger = get_logger("deps")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings.

    Using lru_cache ensures we don't reload .env on every request.
    """
    return settings


def get_logger_instance(name: str = "api"):
    """Return a logger instance."""
    return get_logger(name)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the currently authenticated user from a Bearer token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await session.execute(
        select(User).where(User.id == user_id, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the current user to be a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
