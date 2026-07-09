# AI Document Q&A System

An AI-powered document question-answering system built with **RAG (Retrieval-Augmented Generation)**, **hybrid search**, and **source citations**.

Upload PDFs or paste URLs → ask questions in natural language → get grounded, cited answers.

---

## Features

- [x] **Document ingestion** — upload PDFs or scrape URLs
- [x] **Semantic chunking** — recursive, semantic, and hierarchical strategies with overlap
- [x] **Hybrid search** — vector similarity + BM25 keyword search fusion
- [x] **Re-ranking** — cross-encoder reranker (ms-marco-MiniLM) and optional Cohere Rerank
- [x] **Source citations** — answers cite the document and chunk used
- [x] **Conversation memory** — persistent chat threads with title generation
- [x] **Streaming responses** — real-time answer streaming via SSE
- [x] **Cost tracking dashboard** — per-request and per-conversation token/cost usage
- [x] **Multi-LLM support** — OpenAI, Anthropic Claude, Ollama, and mock fallback
- [x] **Advanced chunking** — parent-document retrieval and enriched chunk metadata
- [x] **Evaluation pipeline** — faithfulness, answer relevance, context precision, and regression detection
- [x] **Authentication** — JWT-based registration/login with protected routes
- [x] **Document management UI** — list, embed, sync, reindex, and delete documents

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16 + React 19 + TypeScript + Tailwind CSS v4 |
| Backend API | Python 3.12 + FastAPI + SQLAlchemy 2 (async) |
| Vector DB | Qdrant |
| Embeddings | OpenAI `text-embedding-3-small` / local `sentence-transformers` |
| LLM | OpenAI GPT-4o / Anthropic Claude / Ollama / Mock |
| Re-ranking | cross-encoder / Cohere Rerank |
| Auth | JWT (OAuth2 password flow) |
| Deployment | Docker + Docker Compose |

---

## Architecture

```
┌─────────────┐      REST/WebSocket      ┌──────────────┐
│  Frontend   │ ◄──────────────────────► │   FastAPI    │
│  (Next.js)  │                          │   Backend    │
└─────────────┘                          └──────┬───────┘
                                                │
        ┌─────────────┬─────────────┬──────────┴──────────┐
        ▼             ▼             ▼                     ▼
   PostgreSQL     Qdrant        Uploads             LLM Providers
   / SQLite     (vectors)      (files)
```

---

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.12+
- Docker (optional, for full stack)

### Local Development

```bash
# 1. Clone and navigate
git clone https://github.com/rockymartinezproject/ai-document-qa.git
cd ai-document-qa

# 2. Backend
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local if the backend is not on http://localhost:8000
npm run dev
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker (Full Stack)

```bash
# Development
docker compose up --build

# Production
docker compose -f docker-compose.prod.yml up --build -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Qdrant Dashboard: http://localhost:6333/dashboard

---

## Environment Variables

### Backend (`backend/.env`)

See [`backend/.env.example`](./backend/.env.example) for the full template.

```bash
# Required for production LLM/embedding quality
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database (defaults to SQLite for local dev)
DATABASE_URL=sqlite+aiosqlite:///./app.db
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/aidocqa

# Vector DB
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=documents

# Auth
SECRET_KEY=change-me-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# LLM defaults
DEFAULT_LLM_PROVIDER=auto
DEFAULT_LLM_MODEL=gpt-4o
```

### Frontend (`frontend/.env.local`)

See [`frontend/.env.example`](./frontend/.env.example).

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## API Overview

All routes are prefixed with `/api`.

| Tag | Routes |
|-----|--------|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Documents | `POST /documents/upload`, `POST /documents/url`, `GET /documents`, `DELETE /documents/{id}` |
| Chunks | `GET /chunks?document_id=...` |
| Embeddings | `POST /embed/{document_id}`, `GET /status` |
| Search | `POST /search`, `POST /search/sync/{document_id}`, `GET /status` |
| Chat | `POST /chat/ask`, `POST /chat/stream` |
| Conversations | `GET /conversations`, `POST /conversations`, `GET /conversations/{id}`, `DELETE /conversations/{id}` |
| Usage | `GET /usage`, `GET /usage/breakdown` |
| Providers | `GET /providers` |
| Evaluation | `POST /evaluate/metrics`, `POST /evaluate/runs`, `GET /evaluate/runs` |
| Health | `GET /health` |

---

## Development Commands

Use the included [`Makefile`](./Makefile):

```bash
make backend         # Start FastAPI dev server
make frontend        # Start Next.js dev server
make docker-up       # Start full dev stack with Docker
make docker-up-prod  # Start production stack with Docker
make docker-down     # Stop Docker stack
make test-backend    # Run backend tests
make lint-backend    # Lint backend code with ruff
make lint-frontend   # Lint frontend code
make format-backend  # Format backend code with black
```

---

## Testing

```bash
# Backend
cd backend
pytest -q

# Frontend linting
cd frontend
npm run lint
```

---

## Deployment

See [`DEPLOY.md`](./DEPLOY.md) for step-by-step deployment guides for:

- Self-hosting with Docker Compose
- Render
- Railway
- Vercel (frontend only)

---

## Project Structure

```
ai-document-qa/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/       # API routes
│   │   ├── core/      # Config, logging, security
│   │   ├── models/    # Pydantic/SQLAlchemy models
│   │   ├── services/  # Business logic (chunking, embeddings, RAG, LLM)
│   │   └── utils/     # Helpers
│   ├── tests/         # Pytest suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/          # Next.js application
│   ├── app/           # App router pages
│   ├── components/    # React components
│   ├── lib/           # API clients, hooks, utils
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml          # Dev stack
├── docker-compose.prod.yml     # Production stack
├── Makefile                    # Common dev commands
├── README.md
└── DEPLOY.md
```

---

## 30-Day Development Plan

See [`30-DAY-PLAN.md`](./30-DAY-PLAN.md) for the day-by-day commit roadmap.

---

## License

MIT
