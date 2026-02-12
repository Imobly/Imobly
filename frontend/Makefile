.PHONY: help setup run-dev stop clean health

help:
	@echo "🚀 Frontend Makefile"
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
	@curl -f http://localhost:3000 && echo "✅ Service is healthy" || echo "❌ Service is down"
