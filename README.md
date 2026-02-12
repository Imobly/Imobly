# Imobly - Monorepo

Sistema completo de gestão imobiliária

## 📦 Estrutura do Projeto

```
Imobly/
├── backend/          # FastAPI Python (porta 8000)
├── frontend/         # Next.js 14 (porta 3000)
├── docs/             # Documentação centralizada
├── .github/          # CI/CD workflows
├── docker-compose.yml
├── Makefile          # Comandos simplificados
└── SETUP.md          # ← Guia completo de configuração
```

## 🚀 Quick Start

### Pré-requisitos

- Docker & Docker Compose
- Conta no Supabase (obrigatório)
- Python 3.11+ (opcional, para dev local)
- Node.js 18+ & pnpm (opcional, para dev local)

### 1. Configurar Variáveis de Ambiente

```bash
# Copiar template (se ainda não existe .env)
cp .env.example .env

# Editar .env na RAIZ do projeto
# Preencha com suas credenciais do Supabase:
# - SUPABASE_URL
# - SUPABASE_ANON_KEY  
# - SUPABASE_SERVICE_ROLE_KEY
# - DATABASE_URL (Connection Pooling - porta 6543)
# - SECRET_KEY (gere com: openssl rand -hex 32)
```

**📖 Veja [SETUP.md](SETUP.md) para instruções detalhadas de como obter essas credenciais.**

### 2. Iniciar com Docker (Recomendado)

```bash
# Comando único para iniciar tudo
make run-all-dev

# Ou manualmente:
docker-compose build
docker-compose up -d
```

**Serviços disponíveis:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

### 3. Comandos Make Disponíveis

```bash
make help           # Ver todos os comandos
make run-all-dev    # Iniciar tudo (recomendado)
make stop-all       # Parar serviços
make restart-all    # Reiniciar serviços
make logs-all       # Ver logs em tempo real
make health         # Verificar status dos serviços
make clean          # Limpar containers e cache
make test           # Executar testes
```

### 4. Desenvolvimento Local (sem Docker)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
pnpm install
pnpm dev
```

## 🔐 Autenticação

Este projeto usa **Supabase Auth** para autenticação:

- **Frontend**: Gerenciado via `@supabase/auth-helpers-nextjs`
- **Backend**: Validação JWT via `supabase-py`
- **Google OAuth**: Configurado no Supabase Dashboard (em desenvolvimento)

## 📦 Tecnologias

### Backend
- **FastAPI** - Framework web Python
- **SQLAlchemy** - ORM
- **Supabase** - Auth + Storage
- **PostgreSQL** - Database
- **Pytest** - Testes

### Frontend
- **Next.js 14** - Framework React com App Router
- **TypeScript** - Tipagem estática
- **Tailwind CSS** - Estilização
- **shadcn/ui** - Componentes
- **Supabase JS** - Cliente Supabase

## 🧪 Testes

```bash
# Backend
cd backend
make test

# Frontend
cd frontend
pnpm test
```

## 📝 Scripts Úteis

```bash
# Lint
make lint

# Format
make format

# Build
make build

# Clean
make clean
```

## 🔄 Migração

Este projeto foi migrado de 3 repositórios separados para um monorepo:

- ~~Imobly/auth-api~~ → **Removido** (substituído por Supabase Auth)
- Imobly/Backend → `backend/`
- Imobly/Frontend → `frontend/`
- Imobly/Documentation → `docs/`


## 📄 Licença

Este projeto é privado e confidencial.

---

**Status do Projeto**: 🚧 Em Desenvolvimento

Última atualização: Fevereiro 2026
