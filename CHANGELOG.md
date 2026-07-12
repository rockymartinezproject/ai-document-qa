# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-10

### Added

- **Document ingestion**: upload PDFs and scrape URLs into the system.
- **Semantic chunking engine**: recursive, semantic, and hierarchical chunking with configurable size and overlap.
- **Embedding service**: OpenAI `text-embedding-3-small` integration with a local `sentence-transformers` fallback.
- **Vector database**: Qdrant integration with collection management, upsert, and hybrid filters.
- **Basic RAG pipeline**: query → embed → retrieve → generate with source-aware context.
- **Query API v1**: synchronous `/api/chat/ask` endpoint with conversation memory.
- **Streaming responses**: real-time answer streaming via `/api/chat/stream` using SSE.
- **Hybrid search**: vector similarity combined with BM25 keyword search fusion.
- **Re-ranking layer**: cross-encoder reranker with optional Cohere Rerank support.
- **Source citations**: answers cite the originating document and chunk.
- **Conversation memory**: persistent chat threads with auto-generated titles.
- **Chat UI v1**: message threads, streaming text, and loading states.
- **Document management UI**: list, embed, sync, reindex, and delete documents.
- **Cost tracking**: per-request and per-conversation token usage and cost estimation.
- **Cost dashboard**: usage charts, model/conversation breakdowns, and time filters.
- **Multi-LLM support**: unified provider interface for OpenAI, Anthropic Claude, Ollama, and mock fallback.
- **Authentication**: JWT-based registration/login with protected routes.
- **Evaluation pipeline**: faithfulness, answer relevance, and context precision metrics.
- **Evaluation suite**: dataset generation, batch evaluation runs, scoring dashboard, and regression detection.
- **Provider registry**: runtime provider/model selection with `/api/providers`.
- **Backend test coverage**: pytest suite with async fixtures for core services and API routes.

### Infrastructure

- Docker and Docker Compose development and production stacks.
- Multi-stage Dockerfiles for both backend and frontend.
- GitHub Actions CI pipeline for backend tests and frontend lint/build.
- Makefile with common dev, test, and deployment commands.
- Environment templates for backend, frontend, and Docker Compose.

### Documentation

- Comprehensive `README.md` with features, tech stack, architecture, quick start, API overview, and deployment links.
- `DEPLOY.md` with deployment guides for self-hosting, Render, Railway, and Vercel.
- `ROADMAP-NEXT.md` outlining the next 20-day production and product expansion plan.

[0.1.0]: https://github.com/rockymartinezproject/ai-document-qa/releases/tag/v0.1.0
