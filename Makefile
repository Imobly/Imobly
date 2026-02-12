# ========================================
# Makefile - Imobly Monorepo
# ========================================
# Sistema simplificado usando apenas Supabase
# Não há mais PostgreSQL local ou ambiente HML
# ========================================

.PHONY: help setup run-all-dev stop stop-all logs-all restart-all clean health test ps

# Cores para output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
RESET := \033[0m

help:
	@echo "$(CYAN)╔════════════════════════════════════════╗$(RESET)"
	@echo "$(CYAN)║   Imobly Monorepo - Comandos Make     ║$(RESET)"
	@echo "$(CYAN)╚════════════════════════════════════════╝$(RESET)"
	@echo ""
	@echo "$(GREEN)🚀 Comandos Principais:$(RESET)"
	@echo "  $(CYAN)make setup$(RESET)          - Build dos containers"
	@echo "  $(CYAN)make run-all-dev$(RESET)    - Inicia toda a aplicação"
	@echo "  $(CYAN)make stop$(RESET)           - Para todos os serviços"
	@echo "  $(CYAN)make logs-all$(RESET)       - Visualiza logs de todos os serviços"
	@echo "  $(CYAN)make restart-all$(RESET)    - Reinicia todos os serviços"
	@echo ""
	@echo "$(GREEN)🧹 Utilitários:$(RESET)"
	@echo "  $(CYAN)make clean$(RESET)          - Limpa containers, volumes e cache"
	@echo "  $(CYAN)make health$(RESET)         - Verifica saúde dos serviços"
	@echo "  $(CYAN)make ps$(RESET)             - Lista containers em execução"
	@echo ""
	@echo "$(GREEN)🧪 Testes:$(RESET)"
	@echo "  $(CYAN)make test$(RESET)           - Roda todos os testes"
	@echo "  $(CYAN)make test-backend$(RESET)   - Roda testes do backend"
	@echo "  $(CYAN)make test-frontend$(RESET)  - Roda testes do frontend"
	@echo "  $(CYAN)make lint$(RESET)           - Executa linters"
	@echo ""
	@echo "$(YELLOW)⚠️  IMPORTANTE:$(RESET)"
	@echo "  1. Configure backend/.env e frontend/.env"
	@echo "  2. Execute: $(CYAN)make setup$(RESET)"
	@echo "  3. Depois: $(CYAN)make run-all-dev$(RESET)"
	@echo ""

# ========================================
# Comandos Principais
# ========================================

setup:
	@echo "$(CYAN)═══════════════════════════════════════$(RESET)"
	@echo "$(GREEN)📦 Building Docker Containers$(RESET)"
	@echo "$(CYAN)═══════════════════════════════════════$(RESET)"
	@docker-compose build
	@echo "$(GREEN)✅ Build concluído!$(RESET)"
	@echo "$(YELLOW)💡 Próximo passo: make run-all-dev$(RESET)"

run-all-dev:
	@echo "$(CYAN)═══════════════════════════════════════$(RESET)"
	@echo "$(GREEN)🚀 Iniciando Imobly Development$(RESET)"
	@echo "$(CYAN)═══════════════════════════════════════$(RESET)"
	@if [ ! -f backend/.env ]; then \
		echo "$(RED)❌ Erro: Arquivo backend/.env não encontrado!$(RESET)"; \
		echo "$(YELLOW)💡 Copie backend/.env.example para backend/.env e configure suas credenciais$(RESET)"; \
		exit 1; \
	fi
	@if [ ! -f frontend/.env ]; then \
		echo "$(RED)❌ Erro: Arquivo frontend/.env não encontrado!$(RESET)"; \
		echo "$(YELLOW)💡 Copie frontend/.env.example para frontend/.env e configure suas credenciais$(RESET)"; \
		exit 1; \
	fi
	@echo "$(CYAN)🔄 Starting services...$(RESET)"
	@docker-compose up -d
	@echo ""
	@echo "$(GREEN)✅ Aplicação iniciada com sucesso!$(RESET)"
	@echo ""
	@echo "$(CYAN)🌐 URLs disponíveis:$(RESET)"
	@echo "  Backend:  $(GREEN)http://localhost:8000$(RESET)"
	@echo "  Frontend: $(GREEN)http://localhost:3000$(RESET)"
	@echo "  API Docs: $(GREEN)http://localhost:8000/docs$(RESET)"
	@echo ""
	@echo "$(YELLOW)💡 Use 'make logs-all' para ver os logs$(RESET)"

stop:
	@echo "$(YELLOW)🛑 Parando todos os serviços...$(RESET)"
	@docker-compose down
	@echo "$(GREEN)✅ Serviços parados$(RESET)"

stop-all: stop

restart-all:
	@echo "$(YELLOW)🔄 Reiniciando todos os serviços...$(RESET)"
	@docker-compose restart
	@echo "$(GREEN)✅ Serviços reiniciados$(RESET)"

logs-all:
	@echo "$(CYAN)📋 Exibindo logs (Ctrl+C para sair)...$(RESET)"
	@docker-compose logs -f

# ========================================
# Setup e Build
# ========================================

clean:
	@echo "$(YELLOW)🧹 Limpando ambiente...$(RESET)"
	@docker-compose down -v 2>/dev/null || true
	@docker system prune -f
	@echo "$(CYAN)Limpando cache do backend...$(RESET)"
	@cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@cd backend && find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@cd backend && find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Limpeza concluída!$(RESET)"

# ========================================
# Testes
# ========================================

test:
	@echo "$(CYAN)🧪 Executando todos os testes...$(RESET)"
	@$(MAKE) test-backend
	@$(MAKE) test-frontend

test-backend:
	@echo "$(CYAN)🧪 Testes do Backend...$(RESET)"
	@cd backend && pytest -v --cov=app --cov-report=term-missing

test-frontend:
	@echo "$(CYAN)🧪 Testes do Frontend...$(RESET)"
	@cd frontend && pnpm test

lint:
	@echo "$(CYAN)🔍 Executando linters...$(RESET)"
	@cd backend && flake8 app || true
	@cd frontend && pnpm lint || true

# ========================================
# Utilidades
# ========================================

ps:
	@echo "$(CYAN)📊 Containers em execução:$(RESET)"
	@docker-compose ps

health:
	@echo "$(CYAN)🏥 Verificando saúde dos serviços...$(RESET)"
	@echo ""
	@echo -n "Backend:  "
	@curl -s -f http://localhost:8000/health > /dev/null && echo "$(GREEN)✅ OK$(RESET)" || echo "$(RED)❌ DOWN$(RESET)"
	@echo -n "Frontend: "
	@curl -s -f http://localhost:3000 > /dev/null && echo "$(GREEN)✅ OK$(RESET)" || echo "$(RED)❌ DOWN$(RESET)"
	@echo ""
