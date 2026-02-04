# Makefile para Imobly Monorepo

.PHONY: help setup dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend lint-frontend format clean build

# Cores para output
CYAN := \033[0;36m
RESET := \033[0m

help:
	@echo "$(CYAN)Comandos disponíveis:$(RESET)"
	@echo "  make setup          - Instalar todas as dependências"
	@echo "  make dev            - Iniciar ambiente de desenvolvimento (Docker)"
	@echo "  make dev-backend    - Iniciar apenas backend (local)"
	@echo "  make dev-frontend   - Iniciar apenas frontend (local)"
	@echo "  make test           - Executar todos os testes"
	@echo "  make lint           - Executar linters"
	@echo "  make format         - Formatar código"
	@echo "  make clean          - Limpar arquivos temporários"
	@echo "  make build          - Build para produção"
	@echo "  make logs           - Ver logs do Docker"
	@echo "  make down           - Parar Docker"

setup:
	@echo "$(CYAN)Instalando dependências do backend...$(RESET)"
	cd backend && pip install -r requirements.txt
	@echo "$(CYAN)Instalando dependências do frontend...$(RESET)"
	cd frontend && pnpm install
	@echo "$(CYAN)Setup completo!$(RESET)"

dev:
	@echo "$(CYAN)Iniciando ambiente de desenvolvimento com Docker...$(RESET)"
	docker-compose up

dev-backend:
	@echo "$(CYAN)Iniciando backend localmente...$(RESET)"
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	@echo "$(CYAN)Iniciando frontend localmente...$(RESET)"
	cd frontend && pnpm dev

test:
	@echo "$(CYAN)Executando testes do backend...$(RESET)"
	cd backend && pytest -v
	@echo "$(CYAN)Executando testes do frontend...$(RESET)"
	cd frontend && pnpm test

test-backend:
	@echo "$(CYAN)Executando testes do backend...$(RESET)"
	cd backend && pytest -v --cov=app --cov-report=html

test-frontend:
	@echo "$(CYAN)Executando testes do frontend...$(RESET)"
	cd frontend && pnpm test

lint:
	@echo "$(CYAN)Linting backend...$(RESET)"
	cd backend && flake8 app
	@echo "$(CYAN)Linting frontend...$(RESET)"
	cd frontend && pnpm lint

lint-backend:
	cd backend && flake8 app

lint-frontend:
	cd frontend && pnpm lint

format:
	@echo "$(CYAN)Formatando código do backend...$(RESET)"
	cd backend && black app && isort app
	@echo "$(CYAN)Formatando código do frontend...$(RESET)"
	cd frontend && pnpm format

clean:
	@echo "$(CYAN)Limpando arquivos temporários...$(RESET)"
	cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd frontend && rm -rf .next node_modules 2>/dev/null || true
	docker-compose down -v
	@echo "$(CYAN)Limpeza concluída!$(RESET)"

build:
	@echo "$(CYAN)Building backend...$(RESET)"
	cd backend && docker build -t imobly-backend:latest .
	@echo "$(CYAN)Building frontend...$(RESET)"
	cd frontend && docker build -t imobly-frontend:latest .

logs:
	docker-compose logs -f

down:
	@echo "$(CYAN)Parando containers...$(RESET)"
	docker-compose down

restart:
	@echo "$(CYAN)Reiniciando containers...$(RESET)"
	docker-compose down
	docker-compose up -d

ps:
	docker-compose ps

# Database
db-migrate:
	@echo "$(CYAN)Executando migrações...$(RESET)"
	cd backend && alembic upgrade head

db-reset:
	@echo "$(CYAN)Resetando banco de dados...$(RESET)"
	docker-compose down -v
	docker-compose up -d db
	sleep 5
	cd backend && alembic upgrade head

# Supabase
supabase-setup:
	@echo "$(CYAN)Configurando Supabase Storage...$(RESET)"
	cd backend && python scripts/setup_supabase_storage.py

# Install
install-dev-tools:
	@echo "$(CYAN)Instalando ferramentas de desenvolvimento...$(RESET)"
	pip install black isort flake8 pytest pytest-cov
	cd frontend && pnpm add -D prettier eslint

# Produção
prod-up:
	@echo "$(CYAN)Iniciando ambiente de produção...$(RESET)"
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.prod.yml down

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f
