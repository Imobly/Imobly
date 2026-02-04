# 🏢 Imobly - Backend API

Sistema de gestão imobiliária completo desenvolvido em Python com FastAPI. Este repositório faz parte de uma arquitetura de microserviços que inclui:

- **Backend** (este repositório): API principal de gestão imobiliária
- **[Auth-API](https://github.com/Imobly/Auth-api)**: Serviço de autenticação e autorização
- **[Frontend](https://github.com/Imobly/Frontend)**: Interface web em React

---

## 📋 Índice

- [Tecnologias](#-tecnologias)
- [Funcionalidades](#-funcionalidades)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Execução](#-instalação-e-execução)
  - [Opção 1: Docker (Recomendado)](#opção-1-docker-recomendado)
  - [Opção 2: Ambiente Virtual](#opção-2-ambiente-virtual-python)
- [Configuração do Banco de Dados](#-configuração-do-banco-de-dados)
- [Testes](#-testes)
- [Deploy em Produção](#-deploy-em-produção)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [API Documentation](#-api-documentation)
- [Contribuindo](#-contribuindo)

---

## 🚀 Tecnologias

- **Python 3.11+**
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para PostgreSQL
- **Pydantic** - Validação de dados
- **PostgreSQL 15** - Banco de dados relacional
- **Alembic** - Migrations de banco de dados
- **Pytest** - Framework de testes
- **Docker & Docker Compose** - Containerização
- **JWT** - Autenticação stateless

---

## ✨ Funcionalidades

- ✅ **Gestão de Propriedades**: CRUD completo com upload de imagens
- ✅ **Gestão de Inquilinos**: Cadastro e documentação de inquilinos
- ✅ **Contratos de Aluguel**: Criação e acompanhamento de contratos
- ✅ **Pagamentos**: Registro e controle de pagamentos
- ✅ **Despesas**: Gestão de despesas das propriedades
- ✅ **Dashboard**: Métricas e estatísticas em tempo real
- ✅ **Notificações**: Sistema de alertas e lembretes
- ✅ **Autenticação JWT**: Integração com Auth-API
- ✅ **Upload de Arquivos**: Documentos e imagens
- ✅ **Validação de Dados**: Schemas Pydantic robustos
- ✅ **Testes Automatizados**: 130+ testes com >90% coverage

---

## 📦 Pré-requisitos

### Para rodar com Docker (Recomendado)
- [Docker](https://docs.docker.com/get-docker/) 20.10+
- [Docker Compose](https://docs.docker.com/compose/install/) 2.0+

### Para rodar sem Docker
- Python 3.11+
- PostgreSQL 15+
- pip/virtualenv

---

## 🔧 Instalação e Execução

### Opção 1: Docker (Recomendado)

**⚠️ IMPORTANTE para usuários do OneDrive:**  
Se o projeto está no OneDrive, mova para outra pasta (ex: `C:\Projetos\`) para evitar erros de `symlink` e permissões.

```bash
# 1. Clone o repositório
git clone https://github.com/Imobly/Backend.git
cd Backend

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais (veja seção "Configuração do Banco")

# 3. Suba os containers
docker compose up -d

# 4. Aguarde a inicialização (30-40 segundos)
docker compose logs -f backend

# 5. Acesse a API
# API: http://localhost:8000
# Docs: http://localhost:8000/api/v1/docs
```

**Comandos úteis:**

```bash
# Ver logs em tempo real
docker compose logs -f backend

# Parar containers
docker compose down

# Parar e limpar banco (⚠️ perde dados)
docker compose down -v

# Reiniciar apenas backend
docker compose restart backend

# Rodar testes
docker compose --profile test up test-runner

# Acessar shell do container
docker compose exec backend bash
```

---

### Opção 2: Ambiente Virtual Python

```bash
# 1. Clone o repositório
git clone https://github.com/Imobly/Backend.git
cd Backend

# 2. Crie e ative ambiente virtual
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Instale dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Para desenvolvimento

# 4. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 5. Suba banco PostgreSQL (com Docker)
docker compose up -d postgres

# 6. Execute a aplicação
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. Acesse
# API: http://localhost:8000
# Docs: http://localhost:8000/api/v1/docs
```

---

## 🗄️ Configuração do Banco de Dados

### Ambientes e seletor `ENVIRONMENT`

O projeto usa um único `.env` com seletor de ambiente (`ENVIRONMENT`) e três DSNs:

```env
# Seleção de ambiente
ENVIRONMENT=staging  # development|staging|production

# DSNs por ambiente (Supabase recomendado usando PgBouncer porta 6543)
DATABASE_URL_DEV=postgresql://user:pass@host:6543/db?sslmode=require
DATABASE_URL_HML=postgresql://user:pass@host:6543/db?sslmode=require
DATABASE_URL_PROD=postgresql://user:pass@host:6543/db?sslmode=require

# CORS (separado por vírgula)
BACKEND_CORS_ORIGINS=http://localhost:3000,https://demo.imobly.com
```

No desenvolvimento, os `docker-compose` já sobrepõem `ENVIRONMENT=staging` e usam `DATABASE_URL_HML`.

Documento completo: https://imobly.github.io/Documentation/guides/environments/

### Produção (Supabase)

**⚠️ IMPORTANTE: Use Transaction Mode (porta 6543)**

O Supabase oferece dois modos de conexão:

| Modo | Porta | Limite de Conexões | Recomendação |
|------|-------|-------------------|--------------|
| **Transaction Mode** | 6543 | ~10.000 | ✅ **USE ESTE** |
| Session Mode | 5432 | ~30 | ❌ Evite |

**Como configurar:**

1. Acesse [Supabase Dashboard](https://supabase.com/dashboard)
2. Vá em: **Project → Database → Connection String**
3. Copie o **Connection Pooling** (Transaction Mode)
4. Substitua `[YOUR-PASSWORD]` pela sua senha
5. **Importante:** Mude a porta de `5432` para `6543`

```env
# .env (Produção)
ENVIRONMENT=production
DATABASE_URL_PROD=postgresql://postgres.yyeldattafklyutbbnhu:[SUA_SENHA]@aws-0-us-west-2.pooler.supabase.com:6543/postgres
```

**Por que usar Transaction Mode?**
- ✅ Evita erro `max clients reached`
- ✅ Suporta muito mais conexões simultâneas
- ✅ Ideal para ambientes de produção com múltiplas instâncias

---

## 🧪 Testes

### Rodar Testes com Docker

```bash
# Testes + Linting completo
docker compose --profile test up test-runner

# Apenas testes
docker compose --profile test run --rm test-runner pytest -v

# Testes com coverage
docker compose --profile test run --rm test-runner pytest --cov=app --cov-report=html
```

### Rodar Testes Localmente

```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Todos os testes
pytest -v

# Testes com coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# Testes específicos
pytest tests/unit/test_properties.py -v
pytest tests/integration/ -v

# Linting
black --check app tests
isort --check app tests
flake8 app tests
mypy app
```

**Relatório de Coverage:**  
Após rodar testes com `--cov-report=html`, abra: `htmlcov/index.html`

**Status Atual:**
- ✅ 130+ testes
- ✅ >90% coverage
- ✅ CI/CD com GitHub Actions

---

## 🚀 Deploy em Produção

### Render.com (Recomendado)

O repositório já possui `render.yaml` configurado.

**1. Configure no Render Dashboard:**

```bash
# Variáveis de Ambiente Obrigatórias:

DATABASE_URL=postgresql://postgres.xxx:[SENHA]@xxx.supabase.com:6543/postgres
SECRET_KEY=[gere com: python -c "import secrets; print(secrets.token_urlsafe(32))"]
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
DEBUG=false
```

**2. Deploy Automático:**

O deploy acontece automaticamente a cada push na branch `main`.

**3. URLs de Produção:**

- Backend: https://backend-non0.onrender.com
- Auth-API: https://auth-api-3zxk.onrender.com
- Frontend: https://imobly.onrender.com
- Swagger: https://backend-non0.onrender.com/api/v1/docs

### Outras Plataformas

O projeto funciona em qualquer plataforma que suporte Docker:
- Railway
- Fly.io
- Heroku (com Dockerfile)
- DigitalOcean App Platform
- AWS ECS/Fargate

---

## 📁 Estrutura do Projeto

```
Backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Entrypoint da aplicação
│   ├── api/
│   │   ├── __init__.py
│   │   └── api.py                 # Agregador de rotas
│   ├── core/
│   │   ├── config.py              # Configurações (Pydantic)
│   │   ├── security.py            # JWT, hashing
│   │   └── middleware.py          # CORS, error handling
│   ├── db/
│   │   ├── base.py                # Base SQLAlchemy
│   │   ├── session.py             # Engine & SessionLocal
│   │   ├── all_models.py          # Import de todos os models
│   │   └── base_repository.py     # Repository pattern base
│   └── src/
│       ├── properties/            # Módulo de propriedades
│       │   ├── models.py
│       │   ├── schemas.py
│       │   ├── repository.py
│       │   ├── controller.py
│       │   └── router.py
│       ├── tenants/               # Módulo de inquilinos
│       ├── contracts/             # Módulo de contratos
│       ├── payments/              # Módulo de pagamentos
│       ├── expenses/              # Módulo de despesas
│       ├── dashboard/             # Módulo de dashboard
│       └── notifications/         # Módulo de notificações
├── tests/
│   ├── conftest.py                # Fixtures pytest
│   ├── unit/                      # Testes unitários
│   ├── integration/               # Testes de integração
│   └── parametrized/              # Testes parametrizados
├── migrations/                    # Alembic migrations
├── scripts/                       # Scripts utilitários
├── docs/                          # Documentação extra
├── Dockerfile                     # Multi-stage (dev/test/prod)
├── docker-compose.yml             # Orquestração local
├── render.yaml                    # Configuração Render
├── requirements.txt               # Dependências produção
├── requirements-dev.txt           # Dependências desenvolvimento
├── pyproject.toml                 # Configurações Python tools
├── .env.example                   # Template de variáveis
├── Makefile                       # Comandos utilitários
└── README.md                      # Este arquivo
```

---

## 📚 API Documentation

### Swagger UI (Interativo)

Acesse: http://localhost:8000/api/v1/docs

### ReDoc (Documentação Limpa)

Acesse: http://localhost:8000/api/v1/redoc

### OpenAPI Schema (JSON)

Acesse: http://localhost:8000/api/v1/openapi.json

### Documentação Completa

Visite: [https://imobly.github.io/Documentation/](https://imobly.github.io/Documentation/)

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add: nova funcionalidade X'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

**Padrões:**

- Commits: [Conventional Commits](https://www.conventionalcommits.org/)
- Code Style: Black (line-length 100), isort, flake8
- Type Hints: mypy
- Testes: pytest (mínimo 80% coverage)

---

## 📝 Licença

Este projeto é privado e pertence à organização **Imobly**.

---

## 👥 Autores

- **João Vitor** - [GitHub](https://github.com/Imobly)

---

## 🔗 Links Úteis

- **Repositórios Relacionados:**
  - [Auth-API](https://github.com/Imobly/Auth-api)
  - [Frontend](https://github.com/Imobly/Frontend)
  - [Documentação](https://github.com/Imobly/Documentation)

- **Produção:**
  - Backend: https://backend-non0.onrender.com
  - Auth-API: https://auth-api-3zxk.onrender.com
  - Frontend: https://imobly.onrender.com

- **Ferramentas:**
  - [FastAPI Docs](https://fastapi.tiangolo.com/)
  - [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
  - [Pydantic Docs](https://docs.pydantic.dev/)
  - [Supabase Docs](https://supabase.com/docs)

---

## 📞 Suporte

Para dúvidas ou problemas:

1. Abra uma [Issue](https://github.com/Imobly/Backend/issues)
2. Consulte a [Documentação](https://imobly.github.io/Documentation/)
3. Verifique os logs: `docker compose logs -f backend`

---

**Desenvolvido com ❤️ pela equipe Imobly**
