# Deployment Guide

This document covers how to deploy the AI Document Q&A system to common hosting platforms.

---

## Table of Contents

1. [Self-hosting with Docker Compose](#self-hosting-with-docker-compose)
2. [Render](#render)
3. [Railway](#railway)
4. [Vercel (frontend only)](#vercel-frontend-only)

---

## Self-hosting with Docker Compose

The easiest self-hosted option is to run the production compose stack on a VPS, cloud VM, or dedicated server.

### Requirements

- Docker + Docker Compose v2
- A server with at least **2 vCPU / 4 GB RAM** (more if using local embeddings/LLMs)
- (Optional) A domain name and reverse proxy (Nginx, Traefik, Caddy)

### Steps

1. **Clone the repo**

   ```bash
   git clone https://github.com/rockymartinezproject/ai-document-qa.git
   cd ai-document-qa
   ```

2. **Create environment files**

   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env.local
   ```

   Edit both files. At minimum set:

   ```bash
   # backend/.env
   ENVIRONMENT=production
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/aidocqa
   QDRANT_HOST=qdrant
   QDRANT_PORT=6333
   SECRET_KEY=<generate-a-strong-random-secret>
   OPENAI_API_KEY=sk-...
   CORS_ORIGINS=["https://your-frontend-domain.com"]
   ```

   ```bash
   # frontend/.env.local
   NEXT_PUBLIC_API_URL=https://your-backend-domain.com
   ```

3. **Start the production stack**

   ```bash
   docker compose -f docker-compose.prod.yml up --build -d
   ```

4. **Verify**

   - Backend health: `https://your-backend-domain.com/api/health`
   - API docs: `https://your-backend-domain.com/docs`
   - Frontend: `https://your-frontend-domain.com`
   - Qdrant dashboard (do not expose publicly): `http://localhost:6333/dashboard`

### SSL / Reverse Proxy

If you expose the app publicly, put a reverse proxy in front and terminate TLS there. Example Caddyfile:

```caddy
your-backend-domain.com {
    reverse_proxy localhost:8000
}

your-frontend-domain.com {
    reverse_proxy localhost:3000
}
```

### Updating

```bash
cd ai-document-qa
git pull
docker compose -f docker-compose.prod.yml up --build -d
```

---

## Render

### Backend (Web Service)

1. Create a new **Web Service** in Render and connect your GitHub repo.
2. Select the **Docker** runtime.
3. Set the root directory to `backend`.
4. Add environment variables from `backend/.env.example`:
   - `ENVIRONMENT=production`
   - `DATABASE_URL` — use a Render PostgreSQL instance URL
   - `QDRANT_HOST` — use a managed Qdrant cluster or run Qdrant as another Render service
   - `SECRET_KEY`
   - `OPENAI_API_KEY`
   - `CORS_ORIGINS` — e.g. `["https://your-frontend-domain.onrender.com"]`
5. Deploy. Render will use the `backend/Dockerfile`.

### Qdrant on Render

Option A: use [Qdrant Cloud](https://qdrant.tech/cloud/) and set `QDRANT_HOST` / `QDRANT_PORT` / API key.

Option B: deploy Qdrant as a separate **Web Service** with Docker using the official image `qdrant/qdrant:v1.12.1` and a persistent disk.

### Frontend (Web Service)

1. Create a new **Web Service** and connect the same repo.
2. Select the **Docker** runtime.
3. Set the root directory to `frontend`.
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL=https://your-backend-service.onrender.com`
5. Deploy. Render will use the `frontend/Dockerfile`.

---

## Railway

Railway works best when you deploy each service separately and connect them.

### 1. Create a new project

Connect your GitHub repo to Railway.

### 2. Add PostgreSQL and Qdrant

- Add a **PostgreSQL** service from the Railway template.
- Add a **Qdrant** service by deploying the `qdrant/qdrant:v1.12.1` image, or use Qdrant Cloud.

### 3. Deploy the Backend

- Create a service and set the source to your repo.
- Set the service **Start Command** to use the backend Dockerfile, or let Railway auto-detect it by pointing the service at the `backend` directory.
- Add environment variables:
  - `ENVIRONMENT=production`
  - `DATABASE_URL` — reference the Railway Postgres variable, e.g. `${{Postgres.DATABASE_URL}}` (swap `postgres://` to `postgresql+asyncpg://`)
  - `QDRANT_HOST` — internal hostname of your Qdrant service
  - `QDRANT_PORT=6333`
  - `SECRET_KEY`
  - `OPENAI_API_KEY`
  - `CORS_ORIGINS=["https://your-frontend-domain.up.railway.app"]`

### 4. Deploy the Frontend

- Create another service and point it at the `frontend` directory.
- Add environment variable:
  - `NEXT_PUBLIC_API_URL=https://your-backend-service.up.railway.app`

### 5. Generate a domain

Railway can generate public domains for each service under **Settings → Domains**.

---

## Vercel (frontend only)

Vercel is a convenient place to host the Next.js frontend. You will still need a separate backend deployment.

1. Push the repo to GitHub.
2. In Vercel, import the project and select the `frontend` directory as the root.
3. Set the framework preset to **Next.js**.
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL=https://your-backend-domain.com`
5. Deploy.

> Note: the backend cannot run on Vercel because it requires a persistent server, a database, and Qdrant. Deploy the backend to Render, Railway, Fly.io, or a VPS.

---

## Production Checklist

Before going live, make sure you have:

- [ ] Changed `SECRET_KEY` to a strong random value.
- [ ] Set `ENVIRONMENT=production`.
- [ ] Switched from SQLite to PostgreSQL.
- [ ] Configured `CORS_ORIGINS` to only allow your frontend domain.
- [ ] Added your LLM/embedding API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.).
- [ ] Set up a managed or self-hosted Qdrant instance.
- [ ] Configured `NEXT_PUBLIC_API_URL` to point at your backend.
- [ ] Enabled TLS (HTTPS) on public domains.
- [ ] Restricted public access to Qdrant (port 6333).
- [ ] Configured log rotation and disk monitoring for uploads.

---

## Troubleshooting

- **Backend health check fails**: check that `DATABASE_URL` and `QDRANT_HOST` are reachable from the backend container/service.
- **Frontend cannot reach backend**: verify `NEXT_PUBLIC_API_URL` and `CORS_ORIGINS` include the frontend domain.
- **SQLite in production**: SQLite works for local development but should be replaced with PostgreSQL for production.
- **No API keys set**: the app falls back to a mock LLM and local embeddings, which is fine for testing but not useful for real Q&A.
