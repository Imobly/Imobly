.PHONY: help setup setup-dev run run-dev stop stop-dev restart-dev pull clean deploy health

help:
	@echo "🚀 Frontend Makefile Commands"
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
	@echo "✅ Frontend deployed successfully!"

# Utilidades
pull:
	git pull origin develop

clean:
	docker compose -f docker-compose.yml down -v 2>/dev/null || true
	docker compose -f docker-compose.prod.yml down -v 2>/dev/null || true
	docker system prune -f

health:
	@curl -f http://localhost:3000 && echo "✅ Service is healthy" || echo "❌ Service is down"
