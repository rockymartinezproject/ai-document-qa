# AI Document Q&A System

An AI-powered document question-answering system built with **RAG (Retrieval-Augmented Generation)**, **vector search**, and **source citations**.

Upload documents (PDFs, URLs) → ask questions in natural language → get grounded, cited answers.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Backend API | Python + FastAPI |
| Vector DB | Qdrant |
| Embeddings | OpenAI `text-embedding-3-small` / sentence-transformers |
| LLM | OpenAI GPT-4o / Claude 3.5 / Local via Ollama |
| Orchestration | LangChain |
| Deployment | Docker + Docker Compose |

## Features

- [ ] Semantic chunking with overlap
- [ ] Hybrid search (vector + BM25 keyword)
- [ ] Re-ranking (cross-encoder / Cohere)
- [ ] Source citations in responses
- [ ] Conversation memory
- [ ] Streaming responses
- [ ] Cost tracking dashboard
- [ ] Evaluation pipeline (RAGAS)

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.12+
- Docker (optional)

### Local Development

```bash
# 1. Clone and navigate
cd ai-document-qa

# 2. Backend
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Docker (Full Stack)

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Qdrant: http://localhost:6333/dashboard

## Project Structure

```
ai-document-qa/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/       # API routes
│   │   ├── core/      # Config, logging
│   │   ├── models/    # Pydantic/SQLAlchemy models
│   │   ├── services/  # Business logic (chunking, embeddings, RAG)
│   │   └── utils/     # Helpers
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/          # Next.js application
│   ├── app/           # App router
│   ├── components/    # React components
│   ├── lib/           # Utils, API clients
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── 30-DAY-PLAN.md     # Daily commit plan
```

## 30-Day Development Plan

See [`30-DAY-PLAN.md`](./30-DAY-PLAN.md) for the day-by-day commit roadmap.

## License

MIT
