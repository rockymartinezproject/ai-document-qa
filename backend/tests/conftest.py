"""Shared test fixtures and helpers."""

from collections.abc import AsyncIterator
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.base import Base, get_db
from app.db.models import User
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def create_test_user(
    session: AsyncSession,
    email: str,
    password: str,
    is_superuser: bool = False,
) -> User:
    """Create and return a test user."""
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        is_active=True,
        is_superuser=is_superuser,
    )
    session.add(user)
    return user


def user_token(user: User) -> str:
    """Return a valid Bearer token for a user."""
    return create_access_token({"sub": user.id})


@pytest_asyncio.fixture
async def db_engine():
    """Create a fresh in-memory async engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session bound to the test engine."""
    async_session = sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[TestClient, None]:
    """Yield a TestClient with DB and auth dependencies overridden."""

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def upload_dir(tmp_path: Path) -> Path:
    """Override the upload directory to a temp path for the duration of the test."""
    original = settings.UPLOAD_DIR
    upload_path = tmp_path / "uploads"
    upload_path.mkdir()
    settings.UPLOAD_DIR = str(upload_path)
    yield upload_path
    settings.UPLOAD_DIR = original
