"""
AI Document Q&A System - FastAPI Backend
"""

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware.request_logging import RequestLoggingMiddleware
from app.api import health

# Setup structured logging on import
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="AI-Powered Document Q&A with RAG, Vector Search, and Source Citations",
    docs_url="/docs",
    redoc_url="/redoc",
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
app.include_router(health.router, prefix="/api", tags=["Health"])


@app.get("/")
async def root():
    return {
        "message": "AI Document Q&A API",
        "docs": "/docs",
        "version": settings.PROJECT_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
