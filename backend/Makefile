.PHONY: help setup run-dev stop test lint format install clean health

help:
	@echo "🚀 Backend Makefile"
	@echo ""
	@echo "⚠️  IMPORTANTE: Para desenvolvimento, use os comandos na RAIZ do projeto:"
	@echo "  cd .."
	@echo "  make setup"
	@echo "  make run-all-dev"
	@echo "  make stop"
	@echo ""
	@echo "📦 Produção (apenas se executado standalone):"
	@echo "  make setup         - Build production container"
	@echo "  make run-dev       - Start production service"
	@echo "  make stop          - Stop production service"
	@echo "  make logs          - View production logs"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test          - Run tests with coverage"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo ""
	@echo "🧹 Utilities:"
	@echo "  make clean         - Clean containers and cache"
	@echo "  make health        - Check service health"

# Produção (standalone)
setup:
	@echo "⚠️  Atenção: Usando docker-compose.prod.yml (produção)"
	@docker compose -f docker-compose.prod.yml build

run-dev:
	@echo "⚠️  Atenção: Usando docker-compose.prod.yml (produção)"
	@docker compose -f docker-compose.prod.yml up -d

stop:
	@docker compose -f docker-compose.prod.yml down

logs:
	@docker compose -f docker-compose.prod.yml logs -f

# Utilidades
clean:
	@echo "🧹 Cleaning..."
	@docker compose -f docker-compose.prod.yml down -v 2>/dev/null || true
	@docker system prune -f

health:
	@curl -f http://localhost:8000/health && echo "✅ Service is healthy" || echo "❌ Service is down"

# Testing & Quality
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest -v --cov=src --cov-report=html --cov-report=term-missing

lint:
	@echo "Running Black..."
	@black --check src tests
	@echo "Running isort..."
	@isort --check src tests
	@echo "Running Flake8..."
	@flake8 src tests

format:
	black src tests
	isort src tests
