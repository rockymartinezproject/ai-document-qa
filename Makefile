.PHONY: help dev backend frontend docker-build docker-up docker-down test test-backend test-frontend lint lint-backend lint-frontend

help:
	@echo "Available commands:"
	@echo "  make backend        - Start FastAPI dev server"
	@echo "  make frontend       - Start Next.js dev server"
	@echo "  make docker-up      - Start full stack with Docker"
	@echo "  make docker-down    - Stop Docker stack"
	@echo "  make test-backend   - Run backend tests"
	@echo "  make test-frontend  - Run frontend tests"
	@echo "  make lint-backend   - Lint backend code"
	@echo "  make lint-frontend  - Lint frontend code"

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down -v

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npm test

lint-backend:
	cd backend && black app/ tests/ && ruff check app/ tests/

lint-frontend:
	cd frontend && npm run lint
