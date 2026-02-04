# Imobly - Monorepo

Sistema completo de gestão imobiliária unificado em um único repositório.

## 📦 Estrutura do Projeto

```
Imobly/
├── backend/          # FastAPI Python (porta 8000)
├── frontend/         # Next.js 14 (porta 3000)
├── docs/             # Documentação centralizada
├── .github/          # CI/CD workflows
└── docker-compose.yml
```

## 🚀 Quick Start

### Pré-requisitos

- Docker & Docker Compose
- Python 3.11+ (para desenvolvimento local do backend)
- Node.js 18+ & pnpm (para desenvolvimento local do frontend)
- Conta no Supabase

### 1. Configurar Variáveis de Ambiente

```bash
# Backend
cp backend/.env.example backend/.env
# Edite backend/.env com suas credenciais Supabase

# Frontend  
cp frontend/.env.local.example frontend/.env.local
# Edite frontend/.env.local com suas credenciais Supabase
```

### 2. Iniciar com Docker (Recomendado)

```bash
# Iniciar todos os serviços
docker-compose up

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# Docs API: http://localhost:8000/docs
```

### 3. Desenvolvimento Local (sem Docker)

#### Backend
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

## 📚 Documentação

- [Guia de Arquitetura](docs/guides/architecture.md)
- [Getting Started](docs/guides/getting-started.md)
- [API Reference](docs/api/reference.md)
- [Deploy Guide](docs/guides/deployment.md)

## 🔐 Autenticação

Este projeto usa **Supabase Auth** para autenticação:

- **Frontend**: Gerenciado via `@supabase/auth-helpers-nextjs`
- **Backend**: Validação JWT via `supabase-py`
- **Google OAuth**: Configurado no Supabase Dashboard

### Configuração do Supabase Auth

1. Acesse [Supabase Dashboard](https://supabase.com/dashboard)
2. Authentication → Settings
3. Configure Google OAuth (opcional)
4. Obtenha as credenciais:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`

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

Ver [MIGRATION_LOG.md](docs/MIGRATION_LOG.md) para detalhes.

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit suas mudanças: `git commit -m 'Add: nova funcionalidade'`
4. Push para a branch: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

## 📄 Licença

Este projeto é privado e confidencial.

## 📧 Contato

- **Organização**: [Imobly](https://github.com/Imobly)
- **Issues**: [GitHub Issues](https://github.com/Imobly/Imobly/issues)

---

**Status do Projeto**: 🚧 Em Desenvolvimento

Última atualização: Fevereiro 2026
