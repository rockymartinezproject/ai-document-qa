# 30-Day Commit Plan: AI Document Q&A System

> One commit per day. Each day has a clear, demo-ready milestone.

---

## Week 1: Foundation & Core Pipeline

| Day | Commit Focus | What Gets Done |
|-----|-------------|----------------|
| **1** | **Initial project scaffold** | Monorepo structure, Docker, Next.js + FastAPI skeleton, README, this plan |
| **2** | **FastAPI backend bootstrap** | Health endpoints, project config, logging middleware, dependency injection setup |
| **3** | **Next.js frontend shell** | Layout, navigation, theme (Tailwind), basic pages: Home, Chat, Upload, Dashboard |
| **4** | **Document upload API** | `/api/documents/upload` — PDF text extraction (PyPDF2/pdfplumber), file validation, metadata storage |
| **5** | **URL ingestion API** | `/api/documents/url` — scrape web pages (httpx + BeautifulSoup), extract clean article text |
| **6** | **Semantic chunking engine** | Recursive chunking with overlap, configurable chunk size/overlap, chunk metadata preservation |
| **7** | **Embedding service** | OpenAI `text-embedding-3-small` integration + local `sentence-transformers` fallback, embedding caching |

## Week 2: Vector Search & RAG

| Day | Commit Focus | What Gets Done |
|-----|-------------|----------------|
| **8** | **Vector database setup** | Qdrant (Docker) integration, collection schemas, upsert/search operations, hybrid filter support |
| **9** | **Basic RAG pipeline** | LangChain retrieval chain: query → embed → vector search → prompt → LLM answer |
| **10** | **Query API v1** | `/api/chat/ask` — basic RAG endpoint, synchronous response, error handling |
| **11** | **Upload UI** | Drag-and-drop PDF upload, URL input form, progress indicators, toast notifications |
| **12** | **Chat UI v1** | Message thread component, user/assistant bubbles, input box, basic loading states |
| **13** | **Hybrid search** | BM25 keyword search + vector search fusion (rank fusion or weighted combination) |
| **14** | **Re-ranking layer** | Cross-encoder re-ranker (ms-marco-MiniLM) or Cohere Rerank API, top-k refinement |

## Week 3: Production Features

| Day | Commit Focus | What Gets Done |
|-----|-------------|----------------|
| **15** | **Source citations** | Retrieve chunk sources, inject into prompt, parse citations in response, cite by document+page |
| **16** | **Streaming backend** | SSE streaming from FastAPI, token-by-token LLM streaming via OpenAI/Claude |
| **17** | **Streaming frontend** | Consume SSE in React, real-time text rendering, streaming cursor, abort controller |
| **18** | **Conversation memory** | PostgreSQL/SQLite chat history, message persistence, session/thread management |
| **19** | **Chat history UI** | Sidebar with conversation list, new chat button, rename/delete threads, persistent sessions |
| **20** | **Cost tracking backend** | Token counting per request, price estimation, usage aggregation per conversation/day |
| **21** | **Cost dashboard UI** | Usage charts (Recharts), token spend table, model breakdown, daily/weekly filters |
| **22** | **Multi-LLM support** | Unified LLM provider interface: OpenAI GPT-4o, Claude 3.5, Ollama local models, switchable at runtime |

## Week 4: Quality, Evaluation & Polish

| Day | Commit Focus | What Gets Done |
|-----|-------------|----------------|
| **23** | **Advanced chunking** | Semantic chunking (sentence-transformer similarity), hierarchical chunking, parent-document retrieval |
| **24** | **Evaluation pipeline setup** | RAGAS integration or custom metrics: faithfulness, answer relevance, context precision |
| **25** | **Evaluation suite** | Test dataset generation, batch evaluation runner, scoring dashboard, regression detection |
| **26** | **Docker & DevOps polish** | Optimized multi-stage Dockerfiles, docker-compose with Qdrant/Postgres, health checks, Makefile |
| **27** | **Authentication** | OAuth2 / JWT auth (optional but nice), user isolation, protected routes, API key management |
| **28** | **Document management UI** | Document list view, delete documents, re-index, metadata editing, search within documents |
| **29** | **Testing & QA** | Pytest backend tests, Jest frontend tests, integration tests for RAG pipeline, bug fixes |
| **30** | **Final polish & deploy docs** | README with screenshots, deployment guides (Render/Railway/Vercel), environment templates, demo video prep |

---

## Commit Message Convention

```
Day N: Short description

- Bullet of what changed
- Another bullet
```

Example:
```
Day 8: Add Qdrant vector database integration

- Set up Qdrant client and collection management
- Implement document upsert with metadata
- Add vector similarity search with filters
- Include Qdrant in docker-compose
```

---


