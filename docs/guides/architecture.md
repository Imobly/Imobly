# 🏗️ Arquitetura do Sistema

Este documento descreve a arquitetura técnica do Imobly, um sistema de gestão imobiliária baseado em microserviços.

---

## 🎯 Visão Geral

O Imobly é construído seguindo uma arquitetura de **microserviços desacoplados**, onde cada serviço tem responsabilidade única e se comunica via HTTP/REST.

```mermaid
graph TB
    User[👤 Usuário] --> Frontend[🎨 Frontend<br/>Next.js]
    Frontend --> AuthAPI[🔐 Auth API<br/>FastAPI]
    Frontend --> Backend[⚙️ Backend API<br/>FastAPI]
    Backend --> AuthAPI
    AuthAPI --> AuthDB[(🗄️ Auth DB<br/>PostgreSQL)]
    Backend --> BackendDB[(🗄️ Backend DB<br/>PostgreSQL)]
```

---

## 📦 Componentes

### 🔐 Auth API (Porta 8001)

**Responsabilidades:**
- Gerenciamento de usuários (registro, login, atualização)
- Autenticação via JWT
- Emissão e validação de tokens
- Controle de sessões

**Stack Tecnológica:**
- FastAPI (Python 3.11)
- PostgreSQL 15
- JWT (python-jose, HS256)
- Pydantic (validação)
- SQLAlchemy (ORM)

**Endpoints Principais:**
- `POST /api/v1/auth/register` - Criar usuário
- `POST /api/v1/auth/login` - Fazer login
- `GET /api/v1/auth/me` - Obter usuário logado
- `PUT /api/v1/auth/me` - Atualizar perfil

**Banco de Dados:**
```
auth_db
├── users (id, email, username, hashed_password, full_name, created_at, updated_at)
```

---

### ⚙️ Backend API (Porta 8000)

**Responsabilidades:**
- Gestão de propriedades (CRUD)
- Gestão de contratos e locatários
- Gestão de cobranças e pagamentos
- Dashboard e relatórios
- Upload de documentos

**Stack Tecnológica:**
- FastAPI (Python 3.11)
- PostgreSQL 15
- JWT validation (python-jose)
- SQLAlchemy (ORM)
- Alembic (migrações)

**Endpoints Principais:**
- `GET/POST /api/v1/properties/` - Propriedades
- `GET/POST /api/v1/tenants/` - Locatários
- `GET/POST /api/v1/contracts/` - Contratos
- `GET/POST /api/v1/charges/` - Cobranças
- `GET /api/v1/dashboard/summary` - Dashboard

**Banco de Dados:**
```
imovel_gestao
├── properties (id, title, address, price, owner_id, ...)
├── tenants (id, name, email, phone, owner_id, ...)
├── contracts (id, property_id, tenant_id, start_date, end_date, ...)
├── charges (id, contract_id, amount, due_date, status, ...)
└── payments (id, charge_id, amount, paid_at, ...)
```

---

### 🎨 Frontend (Porta 3000)

**Responsabilidades:**
- Interface web responsiva
- Autenticação de usuários
- Visualização de propriedades, contratos, cobranças
- Dashboard interativo
- Upload de arquivos

**Stack Tecnológica:**
- Next.js 14.2.33 (React)
- TypeScript
- Tailwind CSS
- Shadcn/ui (componentes)
- Axios (HTTP client)

**Páginas Principais:**
- `/` - Dashboard
- `/login` - Login
- `/properties` - Listagem de propriedades
- `/tenants` - Listagem de locatários
- `/contracts` - Listagem de contratos
- `/charges` - Listagem de cobranças

---

## 🔐 Fluxo de Autenticação

### 1️⃣ Login

```mermaid
sequenceDiagram
    participant U as 👤 Usuário
    participant F as 🎨 Frontend
    participant A as 🔐 Auth API
    participant D as 🗄️ Auth DB

    U->>F: Preenche username/password
    F->>A: POST /api/v1/auth/login
    A->>D: Consulta usuário
    D-->>A: Dados do usuário
    A->>A: Valida senha (bcrypt)
    A->>A: Gera JWT token
    A-->>F: {access_token, user}
    F->>F: Salva token em localStorage
    F-->>U: Redireciona para dashboard
```

### 2️⃣ Requisição Autenticada

```mermaid
sequenceDiagram
    participant F as 🎨 Frontend
    participant B as ⚙️ Backend API
    participant A as 🔐 Auth API

    F->>B: GET /api/v1/properties/<br/>Authorization: Bearer <token>
    B->>B: Extrai token do header
    B->>B: Valida JWT (SECRET_KEY)
    B->>B: Extrai user_id do token
    B->>B: Consulta propriedades<br/>filtradas por user_id
    B-->>F: Lista de propriedades
```

!!! danger "SECRET_KEY Compartilhada"
    O **Backend** e o **Auth API** devem usar a **MESMA SECRET_KEY** para que o Backend consiga validar os tokens emitidos pelo Auth API.

---

## 🌐 Comunicação entre Serviços

### Frontend → Auth API

**Propósito:** Autenticação de usuários

**Endpoints:**
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `PUT /api/v1/auth/me`

**Autenticação:** Não requerida para login/register, requerida para /me

---

### Frontend → Backend

**Propósito:** Operações de negócio

**Endpoints:**
- Todas as rotas `/api/v1/*` (properties, tenants, contracts, charges, etc)

**Autenticação:** Requerida (Bearer token em todos os requests)

---

### Backend → Auth API

**Propósito:** Validação de tokens (se necessário)

**Nota:** Atualmente o Backend valida tokens localmente usando a SECRET_KEY compartilhada, sem necessidade de consultar o Auth API.

---

## 🗄️ Bancos de Dados

### Desenvolvimento

Cada serviço tem seu próprio banco PostgreSQL:

| Serviço | Host | Porta | Database | Usuário | Senha |
|---------|------|-------|----------|---------|-------|
| Auth API | localhost | 5433 | auth_db | postgres | admin123 |
| Backend | localhost | 5432 | imovel_gestao | postgres | admin123 |
| Backend Test | localhost | 5434 | test_db | postgres | admin123 |

### Produção

Ambos os serviços usam **Supabase** (PostgreSQL gerenciado):

- **Connection Pooler:** Transaction Mode (porta 6543)
- **Direct Connection:** Porta padrão 5432 (não recomendado)

!!! warning "Migração de Dados"
    Em produção, você deve criar os schemas separadamente:
    - Database 1: `auth_db` (tabelas de usuários)
    - Database 2: `imovel_gestao` (tabelas de negócio)

---

## 🐳 Docker & Docker Compose

### Desenvolvimento

Cada repositório tem seu `docker-compose.yml`:

```yaml
# Auth-api/docker-compose.yml
services:
  auth-api:
    build: .
    ports: ["8001:8001"]
    environment:
      - DATABASE_URL=postgresql://postgres:admin123@postgres:5432/auth_db
  postgres:
    image: postgres:15
    ports: ["5433:5432"]
```

```yaml
# Backend/Backend/docker-compose.yml
services:
  backend:
    build: .
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://postgres:admin123@postgres:5432/imovel_gestao
  postgres:
    image: postgres:15
    ports: ["5432:5432"]
```

```yaml
# Frontend/Frontend/docker-compose.yml
services:
  frontend:
    build: .
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_AUTH_API_URL=http://localhost:8001
```

### Produção

Cada repositório tem `docker-compose.prod.yml` que:
- Usa variáveis do `.env.prod`
- Conecta ao Supabase em vez de PostgreSQL local
- Não expõe portas desnecessárias
- Usa healthchecks e restart policies

---

## 🔧 Variáveis de Ambiente Críticas

### Auth API

```bash
# .env (desenvolvimento)
DATABASE_URL=postgresql://postgres:admin123@postgres:5432/auth_db
SECRET_KEY=<chave-de-32-bytes-hex>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# .env.prod (produção)
DATABASE_URL=postgresql://user:pass@host:6543/auth_db?pgbouncer=true
SECRET_KEY=<MESMO-SECRET-DO-BACKEND>
```

### Backend

```bash
# .env (desenvolvimento)
DATABASE_URL=postgresql://postgres:admin123@postgres:5432/imovel_gestao
AUTH_API_SECRET_KEY=<MESMO-SECRET-DO-AUTH-API>
ALGORITHM=HS256

# .env.prod (produção)
DATABASE_URL=postgresql://user:pass@host:6543/imovel_gestao?pgbouncer=true
AUTH_API_SECRET_KEY=<MESMO-SECRET-DO-AUTH-API>
```

### Frontend

```bash
# .env (desenvolvimento)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AUTH_API_URL=http://localhost:8001

# .env.prod (produção)
NEXT_PUBLIC_API_URL=https://api.seudominio.com
NEXT_PUBLIC_AUTH_API_URL=https://auth.seudominio.com
```

---

## 📊 Diagrama Detalhado de Deploy

```mermaid
graph TB
    subgraph "Produção"
        LB[⚖️ Load Balancer<br/>Nginx/Caddy]
        LB --> F[🎨 Frontend<br/>Docker Container]
        LB --> B[⚙️ Backend<br/>Docker Container]
        LB --> A[🔐 Auth API<br/>Docker Container]
        
        A --> SDB1[(☁️ Supabase<br/>auth_db)]
        B --> SDB2[(☁️ Supabase<br/>imovel_gestao)]
    end
    
    subgraph "Desenvolvimento"
        F_DEV[🎨 Frontend<br/>:3000]
        B_DEV[⚙️ Backend<br/>:8000]
        A_DEV[🔐 Auth API<br/>:8001]
        
        A_DEV --> PG1[(🐘 PostgreSQL<br/>:5433)]
        B_DEV --> PG2[(🐘 PostgreSQL<br/>:5432)]
    end
```

---

## 🚀 Escalabilidade

### Horizontal Scaling

Cada serviço pode ser escalado independentemente:

```bash
# Docker Compose (múltiplas instâncias)
docker compose up -d --scale backend=3
docker compose up -d --scale auth-api=2
```

### Load Balancing

Use Nginx ou Caddy para distribuir requisições:

```nginx
upstream backend_api {
    server backend_1:8000;
    server backend_2:8000;
    server backend_3:8000;
}

server {
    location /api/ {
        proxy_pass http://backend_api;
    }
}
```

---

## 🔒 Segurança

### Camadas de Segurança

1. **JWT Tokens:** Expira em 30 minutos
2. **HTTPS:** Obrigatório em produção
3. **CORS:** Configurado para domínios permitidos
4. **SQL Injection:** Prevenido via SQLAlchemy ORM
5. **Password Hashing:** bcrypt com salt automático
6. **Environment Variables:** Segredos nunca no código

### Checklist de Produção

- [ ] SECRET_KEY com 32 bytes aleatórios
- [ ] HTTPS habilitado (TLS 1.2+)
- [ ] CORS configurado corretamente
- [ ] DATABASE_URL com Transaction Mode
- [ ] Logs configurados (não printar tokens)
- [ ] Rate limiting habilitado
- [ ] Firewall configurado (portas 80, 443)

---

## 📚 Referências

- [Getting Started](getting-started.md) - Setup inicial
- [Deployment Guide](deployment.md) - Deploy em produção
- [API Reference](../api/index.md) - Endpoints detalhados
- [Auth Guide](../auth/index.md) - Fluxo de autenticação

---

**📝 Última atualização:** Janeiro 2025  
**🔧 Versão da Stack:** Auth API 1.0 | Backend 1.0 | Frontend 1.0
