# AgentTutor Development Makefile
# Requires: Python 3.11+, Node 18+, npm

.PHONY: help setup setup-backend setup-frontend dev dev-backend dev-frontend \
        db-migrate db-seed test test-backend test-frontend test-e2e \
        lint lint-backend lint-frontend clean

PYTHON := python
PIP := pip
FLASK := flask
NPM := npm

# ── Help ──────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "AgentTutor — Available Commands"
	@echo "================================"
	@echo "  make setup          Install all dependencies"
	@echo "  make dev            Run frontend + backend concurrently"
	@echo "  make dev-backend    Run Flask backend only"
	@echo "  make dev-frontend   Run Vite frontend only"
	@echo "  make db-migrate     Run Alembic migrations"
	@echo "  make db-seed        Seed development data"
	@echo "  make test           Run all tests"
	@echo "  make test-backend   Run pytest"
	@echo "  make test-frontend  Run Vitest"
	@echo "  make lint           Lint all code"
	@echo "  make clean          Remove build artifacts and caches"
	@echo ""

# ── Setup ─────────────────────────────────────────────────────────────────────
setup: setup-backend setup-frontend
	@echo "✅ Setup complete. Copy .env.example to .env and configure it."

setup-backend:
	cd backend && $(PYTHON) -m venv .venv
	cd backend && .venv\Scripts\pip install -r requirements.txt
	@echo "✅ Backend dependencies installed"

setup-frontend:
	cd frontend && $(NPM) install
	@echo "✅ Frontend dependencies installed"

# ── Development ───────────────────────────────────────────────────────────────
dev-backend:
	cd backend && .venv\Scripts\python -m flask --app wsgi:app run --debug --host=0.0.0.0 --port=5000

dev-frontend:
	cd frontend && $(NPM) run dev

# ── Database ──────────────────────────────────────────────────────────────────
db-migrate:
	cd backend && .venv\Scripts\python -m alembic upgrade head

db-seed:
	cd backend && .venv\Scripts\python scripts/seed.py

db-reset:
	cd backend && .venv\Scripts\python -m alembic downgrade base
	cd backend && .venv\Scripts\python -m alembic upgrade head
	cd backend && .venv\Scripts\python scripts/seed.py

# ── Testing ───────────────────────────────────────────────────────────────────
test: test-backend test-frontend

test-backend:
	cd backend && .venv\Scripts\python -m pytest tests/ -v --tb=short

test-frontend:
	cd frontend && $(NPM) run test

test-e2e:
	cd frontend && $(NPM) run test:e2e

# ── Linting ───────────────────────────────────────────────────────────────────
lint: lint-backend lint-frontend

lint-backend:
	cd backend && .venv\Scripts\python -m ruff check app/ tests/
	cd backend && .venv\Scripts\python -m mypy app/ --ignore-missing-imports

lint-frontend:
	cd frontend && $(NPM) run lint

# ── Clean ─────────────────────────────────────────────────────────────────────
clean:
	rd /s /q backend\.venv 2>nul || true
	rd /s /q frontend\node_modules 2>nul || true
	rd /s /q frontend\dist 2>nul || true
	del /s /q backend\**\__pycache__ 2>nul || true

