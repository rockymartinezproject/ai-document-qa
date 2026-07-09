.PHONY: help dev backend frontend docker-up docker-up-prod docker-down docker-logs \
        test test-backend test-frontend lint lint-backend lint-frontend format format-backend

help:
	@echo "Available commands:"
	@echo "  make dev             - Start both backend and frontend dev servers"
	@echo "  make backend         - Start FastAPI dev server"
	@echo "  make frontend        - Start Next.js dev server"
	@echo "  make docker-up       - Start full dev stack with Docker"
	@echo "  make docker-up-prod  - Start production stack with Docker"
	@echo "  make docker-down     - Stop Docker stack"
	@echo "  make docker-logs     - Tail Docker compose logs"
	@echo "  make test            - Run backend tests and frontend lint"
	@echo "  make test-backend    - Run backend tests"
	@echo "  make test-frontend   - Run frontend tests (if configured)"
	@echo "  make lint-backend    - Lint backend code with ruff"
	@echo "  make lint-frontend   - Lint frontend code"
	@echo "  make format-backend  - Format backend code with black"


dev:
	@echo "Starting backend and frontend in parallel..."
	@(trap 'kill 0' EXIT; cd backend && uvicorn app.main:app --reload --port 8000) & \
	 (cd frontend && npm run dev) & \
	 wait

test: test-backend lint-frontend


backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

docker-up:
	docker compose -f docker-compose.yml up --build -d

docker-up-prod:
	docker compose -f docker-compose.prod.yml up --build -d

docker-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v

docker-logs:
	docker compose -f docker-compose.yml logs -f

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npm test

lint-backend:
	cd backend && ruff check app/ tests/

lint-frontend:
	cd frontend && npm run lint

format-backend:
	cd backend && black app/ tests/
