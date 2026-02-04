.PHONY: help setup setup-dev run run-dev stop stop-dev restart-dev pull clean deploy health test lint format install test-docker

help:
	@echo "🚀 Backend Makefile Commands"
	@echo ""
	@echo "📦 Production:"
	@echo "  make setup         - Build production containers"
	@echo "  make run           - Start production services"
	@echo "  make stop          - Stop production services"
	@echo "  make logs          - View production logs"
	@echo "  make deploy        - Full deployment (clean + pull + setup + run)"
	@echo ""
	@echo "🛠️  Development:"
	@echo "  make setup-dev     - Build development containers"
	@echo "  make run-dev       - Start development services"
	@echo "  make stop-dev      - Stop development services"
	@echo "  make restart-dev   - Restart development services"
	@echo "  make logs-dev      - View development logs"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test          - Run tests with coverage"
	@echo "  make test-docker   - Run tests in Docker"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo ""
	@echo "🧹 Utilities:"
	@echo "  make clean         - Clean containers and cache"
	@echo "  make health        - Check service health"

# Produção
setup:
	docker compose -f docker-compose.prod.yml build

run:
	docker compose -f docker-compose.prod.yml up -d

stop:
	docker compose -f docker-compose.prod.yml down

logs:
	docker compose -f docker-compose.prod.yml logs -f

# Desenvolvimento
setup-dev:
	docker compose -f docker-compose.yml build

run-dev:
	docker compose -f docker-compose.yml up -d --remove-orphans

stop-dev:
	docker compose -f docker-compose.yml down

restart-dev:
	docker compose -f docker-compose.yml down
	docker compose -f docker-compose.yml build
	docker compose -f docker-compose.yml up -d --remove-orphans

logs-dev:
	docker compose -f docker-compose.yml logs -f

# Deploy em produção
deploy: clean pull setup run
	@echo "✅ Backend deployed successfully!"

# Utilidades
pull:
	git pull origin main

clean:
	docker compose -f docker-compose.yml down -v 2>/dev/null || true
	docker compose -f docker-compose.prod.yml down -v 2>/dev/null || true
	docker system prune -f

health:
	@curl -f http://localhost:8000/health && echo "✅ Service is healthy" || echo "❌ Service is down"

# Testing & Quality
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

test:
	pytest -v --cov=app --cov-report=html --cov-report=term-missing

test-docker:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
	docker-compose -f docker-compose.test.yml down

lint:
	@echo "Running Black..."
	@black --check app tests
	@echo "Running isort..."
	@isort --check app tests
	@echo "Running Flake8..."
	@flake8 app tests
	@echo "Running MyPy..."
	@mypy app

format:
	black app tests
	isort app tests
