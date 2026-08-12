.PHONY: help setup run-dev stop test lint format install clean health \
        migrate migrate-down migrate-history migration stamp-baseline migrate-sql

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
	@echo "🗄️  Migrations (Alembic):"
	@echo "  make migrate           - Aplicar migrations pendentes (upgrade head)"
	@echo "  make migrate-sql       - Imprimir o SQL sem aplicar (revisão antes do deploy)"
	@echo "  make migrate-down      - Reverter a última migration"
	@echo "  make migrate-history   - Histórico e revisão atual"
	@echo "  make migration m=\"msg\" - Gerar nova migration (autogenerate)"
	@echo "  make stamp-baseline    - Marcar banco EXISTENTE como estando na 0001"
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

# ============================================================
# Migrations (Alembic)
# ------------------------------------------------------------
# Aponte ALEMBIC_DATABASE_URL para a conexão DIRETA do Postgres (porta 5432).
# O pooler do Supabase (6543, transaction pooling) não é adequado para DDL.
# ============================================================
migrate:
	alembic upgrade head

migrate-sql:
	@echo "-- SQL das migrations pendentes (nada é aplicado) --"
	@alembic upgrade head --sql

migrate-down:
	alembic downgrade -1

migrate-history:
	@alembic history --verbose
	@echo "--- Revisão atual no banco ---"
	@alembic current

migration:
ifndef m
	$(error Uso: make migration m="descricao da mudanca")
endif
	alembic revision --autogenerate -m "$(m)"

# Somente para o banco JÁ EXISTENTE: registra a 0001 como aplicada sem rodar DDL.
stamp-baseline:
	@echo "⚠️  Marca o banco atual como estando na revisão 0001 (nenhum DDL é executado)."
	alembic stamp 0001
