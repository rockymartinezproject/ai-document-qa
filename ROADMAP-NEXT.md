# Next Roadmap: Production & Product Expansion

> This picks up after the 30-day plan and covers everything discussed for the next phase.

**Estimated total: ~20 working days** (about 3 weeks, one commit per day).
You can compress it to ~15 days if you combine related items or skip lower-priority features.

---

## Week 5: Demo Polish & Stability

| Day | Focus | What Gets Done |
|-----|-------|----------------|
| **31** | **README polish & demo assets** | Add screenshots, architecture GIF, badges (CI, license, Python/Node versions), quick-start video script |
| **32** | **GitHub Release v0.1.0** | Tag `v0.1.0`, write `CHANGELOG.md`, publish release notes summarizing all 30 days |
| **33** | **E2E test setup** | Install Playwright/Cypress, auth flow tests (register → login → me), integrate into CI |
| **34** | **E2E core user journey** | End-to-end test: upload PDF → ask question → verify streamed answer → check documents list |
| **35** | **Rate limiting & timeouts** | Add request rate limits (SlowAPI/Starlette), socket timeouts on LLM calls, max upload retries |
| **36** | **Admin roles & user management** | `is_superuser` flag, admin-only user list endpoint, basic admin UI |
| **37** | **Observability** | Structured JSON logs, `/metrics` endpoint, request tracing, error alerting hooks |

## Week 6: Architecture & Scale

| Day | Focus | What Gets Done |
|-----|-------|----------------|
| **38** | **Background job queue** | Add Celery/ARQ + Redis (or Redis-compatible) to the stack, define task scaffolding |
| **39** | **Async embedding/indexing** | Move document embedding and vector upsert into background workers; progress endpoint for UI |
| **40** | **Multi-tenant workspaces** | `Workspace` model, membership table, workspace-scoped documents/conversations |
| **41** | **Workspace UI** | Workspace switcher, create/join workspace, isolated document/chat views |
| **42** | **API keys for integrations** | Generate/revoke scoped API keys, protect routes with key auth, UI management page |
| **43** | **File type expansion** | Support DOCX, Markdown, TXT, CSV, and common code files; extract text per format |
| **44** | **Feedback loop** | Thumbs up/down on messages, store feedback, surface in evaluation/ranking |

## Week 7: Production Deploy & Final Hardening

| Day | Focus | What Gets Done |
|-----|-------|----------------|
| **45** | **CI/CD deploy automation** | GitHub Actions workflow to deploy backend/frontend to Render/Railway on push to `main` |
| **46** | **Cloud-agnostic infra scaffold** | Terraform or Helm chart for VPS/cloud deployment (Postgres + Qdrant + app services) |
| **47** | **Production hardening review** | Secrets rotation, TLS enforcement, DB backups, upload scanning, Qdrant network isolation |
| **48** | **Performance tuning** | Embedding batching, response caching, connection pooling, lazy model loading |
| **49** | **Analytics dashboard** | Usage trends, model latency histograms, cost projections, conversation volume over time |
| **50** | **Integration tests & v0.2.0 release** | Full integration suite, final bug bash, tag `v0.2.0`, publish release |

---

## Priority Tiers

If you want a shorter path, do these first:

1. **Must-have for production**: Rate limiting, observability, background jobs, production hardening.
2. **Must-have for credibility**: E2E tests, GitHub Release, README polish.
3. **Nice-to-have growth features**: Workspaces, API keys, file type expansion, feedback loop.
4. **Scale/enterprise**: Terraform/Helm, analytics dashboard.

---

## Suggested Daily Commit Messages

```
Day 31: README screenshots and badges
Day 32: Release v0.1.0 and changelog
Day 33: Playwright E2E setup and auth flow tests
Day 34: End-to-end upload-to-answer test
Day 35: Rate limiting and request timeouts
Day 36: Admin roles and user management
Day 37: Observability and request tracing
Day 38: Background job queue setup
Day 39: Async embedding and indexing workers
Day 40: Workspace data model and isolation
Day 41: Workspace switcher UI
Day 42: API key management
Day 43: Additional file type support
Day 44: Message feedback thumbs up/down
Day 45: GitHub Actions deploy pipeline
Day 46: Terraform/Helm deployment scaffold
Day 47: Production hardening checklist
Day 48: Performance tuning and caching
Day 49: Analytics dashboard
Day 50: Integration tests and v0.2.0 release
```
