"""
Application configuration using Pydantic Settings.
"""

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Project
    PROJECT_NAME: str = "AI Document Q&A"
    PROJECT_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # API Keys (loaded from .env)
    OPENAI_API_KEY: str = ""
    COHERE_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Vector DB
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "documents"
    QDRANT_TIMEOUT: float = 10.0

    # Embeddings
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 128

    # LLM
    DEFAULT_LLM_MODEL: str = "gpt-4o"
    LOCAL_LLM_URL: str = "http://localhost:11434"

    # Reranking
    RERANK_ENABLED: bool = True
    RERANK_PROVIDER: str = "cross_encoder"  # cross_encoder | cohere | none
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    COHERE_RERANK_MODEL: str = "rerank-english-v3.0"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    # Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
