.PHONY: help up down logs ps migrate makemigration superuser shell \
        test test-backend test-frontend lint lint-backend lint-frontend fmt \
        build prod-up prod-down prod-logs install-backend install-frontend clean

COMPOSE      ?= docker compose
COMPOSE_PROD ?= docker compose -f docker-compose.prod.yml
BACKEND_PY   ?= backend/.venv/bin/python

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

# --- dev stack ---------------------------------------------------------------
up: ## Start the dev stack (nginx :8080, api :8000, vite :5173)
	$(COMPOSE) up --build -d
down: ## Stop the dev stack
	$(COMPOSE) down
logs: ## Tail logs
	$(COMPOSE) logs -f --tail=100
ps: ## Show containers
	$(COMPOSE) ps
migrate: ## Apply Alembic migrations inside the backend container
	$(COMPOSE) exec backend alembic upgrade head
makemigration: ## Autogenerate a migration: make makemigration m="add table"
	$(COMPOSE) exec backend alembic revision --autogenerate -m "$(m)"
superuser: ## Create the first superuser from APP_FIRST_SUPERUSER_* or args
	$(COMPOSE) exec backend python /scripts/create_superuser.py $(ARGS)
shell: ## Shell in the backend container
	$(COMPOSE) exec backend sh

# --- local tooling -----------------------------------------------------------
install-backend: ## Create backend venv with dev deps
	cd backend && python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements-dev.txt
install-frontend: ## Install frontend deps
	cd frontend && npm ci

test: test-backend test-frontend ## Run all tests
test-backend: ## pytest (SQLite + fakeredis, no services needed)
	cd backend && .venv/bin/python -m pytest
test-frontend: ## vitest
	cd frontend && npm test

lint: lint-backend lint-frontend ## Lint everything
lint-backend: ## ruff + mypy
	cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy app
lint-frontend: ## eslint + tsc
	cd frontend && npm run lint && npm run typecheck
fmt: ## Auto-format backend
	cd backend && .venv/bin/ruff check --fix . && .venv/bin/ruff format .

build: ## Build production images locally
	$(COMPOSE_PROD) build

# --- production --------------------------------------------------------------
prod-up: ## Pull images, migrate and start the production stack
	$(COMPOSE_PROD) pull
	$(COMPOSE_PROD) run --rm migrate
	$(COMPOSE_PROD) up -d --remove-orphans
prod-down: ## Stop the production stack
	$(COMPOSE_PROD) down
prod-logs: ## Tail production logs
	$(COMPOSE_PROD) logs -f --tail=200

clean: ## Remove caches and build output
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/.mypy_cache frontend/dist frontend/coverage
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
