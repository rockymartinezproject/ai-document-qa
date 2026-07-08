"""
AI Document Q&A System - FastAPI Backend
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, chunks, conversations, documents, embeddings, evaluation, health, providers, search, usage
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import engine
from app.db.models import Base
from app.middleware.request_logging import RequestLoggingMiddleware

# Setup structured logging on import
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="AI-Powered Document Q&A with RAG, Vector Search, and Source Citations",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware (order matters: last added = first executed)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(chunks.router, prefix="/api", tags=["Chunks"])
app.include_router(embeddings.router, prefix="/api", tags=["Embeddings"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(conversations.router, prefix="/api", tags=["Conversations"])
app.include_router(usage.router, prefix="/api", tags=["Usage"])
app.include_router(providers.router, prefix="/api", tags=["Providers"])
app.include_router(evaluation.router, prefix="/api", tags=["Evaluation"])


@app.get("/")
async def root():
    return {
        "message": "AI Document Q&A API",
        "docs": "/docs",
        "version": settings.PROJECT_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
