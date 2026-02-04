# 📚 Documentação do Backend - Imóvel Gestão

Bem-vindo à documentação completa do backend da aplicação de gestão de imóveis.

## 📑 Índice

1. [Introdução](#introdução)
2. [Arquitetura](#arquitetura)
3. [Módulos e Endpoints](#módulos-e-endpoints)
4. [Autenticação](#autenticação)
5. [Banco de Dados](#banco-de-dados)
6. [Testes](#testes)
7. [Desenvolvimento](#desenvolvimento)

## 🎯 Introdução

API RESTful desenvolvida com FastAPI para gerenciamento completo de propriedades, inquilinos, contratos e pagamentos.

**Stack Tecnológica:**
- **Framework:** FastAPI 0.100+
- **Banco de Dados:** PostgreSQL 15
- **ORM:** SQLAlchemy 2.0
- **Autenticação:** JWT (JSON Web Tokens)
- **Validação:** Pydantic V2
- **Testes:** Pytest + Coverage
- **Linting:** Black, isort, Flake8, MyPy
- **Container:** Docker + Docker Compose

## 🏗️ Arquitetura

### Estrutura de Diretórios

```
Backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── api.py              # Agregador de rotas
│   │       └── endpoints/          # [Deprecated]
│   ├── core/
│   │   └── config.py               # Configurações da aplicação
│   ├── db/
│   │   ├── base.py                 # Base do SQLAlchemy
│   │   ├── base_repository.py      # Repository pattern base
│   │   ├── session.py              # Sessão do banco
│   │   └── all_models.py           # Registro de modelos
│   ├── src/                        # Módulos de negócio
│   │   ├── auth/                   # Autenticação JWT
│   │   ├── properties/             # Propriedades
│   │   ├── tenants/                # Inquilinos
│   │   ├── units/                  # Unidades
│   │   ├── contracts/              # Contratos
│   │   ├── payments/               # Pagamentos
│   │   ├── expenses/               # Despesas
│   │   ├── notifications/          # Notificações
│   │   └── dashboard/              # Dashboard/Analytics
│   └── main.py                     # Entrypoint da aplicação
├── tests/                          # Suite de testes
│   ├── unit/                       # Testes unitários
│   ├── integration/                # Testes de integração
│   ├── parametrized/               # Testes parametrizados
│   └── conftest.py                 # Fixtures do pytest
├── docs/                           # Documentação
├── Dockerfile                      # Docker para produção
├── Dockerfile.test                 # Docker para testes
├── docker-compose.yml              # Compose para desenvolvimento
├── docker-compose.test.yml         # Compose para testes
├── requirements.txt                # Dependências de produção
├── requirements-dev.txt            # Dependências de desenvolvimento
└── pyproject.toml                  # Configurações de ferramentas
```

### Padrão de Arquitetura

Cada módulo segue o padrão **Repository-Controller-Router**:

```
src/<module>/
├── __init__.py         # Exports do módulo
├── models.py           # Modelos SQLAlchemy (tabelas)
├── schemas.py          # Schemas Pydantic (validação)
├── repository.py       # Camada de acesso a dados
├── controller.py       # Lógica de negócio
└── router.py           # Endpoints FastAPI
```

**Fluxo de Requisição:**
```
Client → Router → Controller → Repository → Database
                      ↓
                  Validation (Pydantic)
```

## 🔌 Módulos e Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### 1. Autenticação (`/auth`)
**Documentação:** [AUTH_DOCUMENTATION.md](./AUTH_DOCUMENTATION.md)

Sistema completo de autenticação com JWT.

**Endpoints principais:**
- `POST /auth/register` - Criar nova conta
- `POST /auth/login` - Login e obtenção de token
- `GET /auth/me` - Dados do usuário autenticado
- `PUT /auth/me` - Atualizar dados do usuário
- `POST /auth/change-password` - Alterar senha

**Exemplos:** [AUTH_EXAMPLES.md](./AUTH_EXAMPLES.md)

### 2. Propriedades (`/properties`)

Gerenciamento de propriedades (imóveis).

**Endpoints:**
- `GET /properties` - Listar propriedades (com filtros)
- `POST /properties` - Criar propriedade
- `GET /properties/{id}` - Obter propriedade específica
- `PUT /properties/{id}` - Atualizar propriedade
- `DELETE /properties/{id}` - Deletar propriedade
- `GET /properties/status/{status}` - Filtrar por status
- `GET /properties/type/{type}` - Filtrar por tipo

**Campos principais:**
- `name` - Nome do imóvel
- `address`, `neighborhood`, `city`, `state`, `zip_code` - Localização
- `type` - Tipo (apartment, house, commercial, studio)
- `area` - Área em m²
- `bedrooms`, `bathrooms`, `parking_spaces`
- `rent` - Valor do aluguel
- `status` - Status (vacant, occupied, maintenance, inactive)

### 3. Inquilinos (`/tenants`)

Gerenciamento de inquilinos.

**Endpoints:**
- `GET /tenants` - Listar inquilinos
- `POST /tenants` - Criar inquilino
- `GET /tenants/{id}` - Obter inquilino
- `PUT /tenants/{id}` - Atualizar inquilino
- `DELETE /tenants/{id}` - Deletar inquilino
- `GET /tenants/cpf/{cpf}` - Buscar por CPF/CNPJ
- `GET /tenants/search?q={query}` - Buscar por nome/email

**Campos principais:**
- `full_name` - Nome completo
- `email`, `phone` - Contato
- `cpf_cnpj` - CPF ou CNPJ
- `birth_date` - Data de nascimento
- `address` - Endereço completo
- `occupation` - Profissão
- `monthly_income` - Renda mensal

### 4. Unidades (`/units`)

Gerenciamento de unidades (apartamentos individuais).

**Endpoints:**
- `GET /units` - Listar unidades
- `POST /units` - Criar unidade
- `GET /units/{id}` - Obter unidade
- `PUT /units/{id}` - Atualizar unidade
- `DELETE /units/{id}` - Deletar unidade
- `GET /units/property/{property_id}` - Unidades de uma propriedade

**Campos principais:**
- `property_id` - Propriedade pai
- `unit_number` - Número/identificação da unidade
- `floor` - Andar
- `bedrooms`, `bathrooms`
- `area` - Área em m²
- `rent` - Valor do aluguel
- `status` - Status (available, occupied, maintenance)

### 5. Contratos (`/contracts`)

Gerenciamento de contratos de aluguel.

**Endpoints:**
- `GET /contracts` - Listar contratos
- `POST /contracts` - Criar contrato
- `GET /contracts/{id}` - Obter contrato
- `PUT /contracts/{id}` - Atualizar contrato
- `DELETE /contracts/{id}` - Deletar contrato
- `GET /contracts/status/{status}` - Filtrar por status
- `GET /contracts/property/{property_id}` - Contratos de uma propriedade
- `GET /contracts/tenant/{tenant_id}` - Contratos de um inquilino

**Campos principais:**
- `property_id`, `tenant_id` - Relacionamentos
- `start_date`, `end_date` - Período do contrato
- `rent_amount` - Valor do aluguel
- `rent_due_day` - Dia de vencimento
- `deposit_amount` - Valor do depósito
- `status` - Status (active, pending, expired, cancelled)

### 6. Pagamentos (`/payments`)

Gerenciamento de pagamentos de aluguéis.

**Endpoints:**
- `GET /payments` - Listar pagamentos
- `POST /payments` - Criar pagamento
- `GET /payments/{id}` - Obter pagamento
- `PUT /payments/{id}` - Atualizar pagamento
- `DELETE /payments/{id}` - Deletar pagamento
- `GET /payments/status/{status}` - Filtrar por status
- `GET /payments/contract/{contract_id}` - Pagamentos de um contrato

**Campos principais:**
- `contract_id`, `tenant_id`, `property_id` - Relacionamentos
- `amount` - Valor
- `due_date`, `payment_date` - Datas
- `status` - Status (pending, paid, overdue, partial)
- `payment_method` - Método (pix, transfer, credit_card, debit_card, cash, check)
- `fine_amount` - Valor de multa

### 7. Despesas (`/expenses`)

Gerenciamento de despesas das propriedades.

**Endpoints:**
- `GET /expenses` - Listar despesas
- `POST /expenses` - Criar despesa
- `GET /expenses/{id}` - Obter despesa
- `PUT /expenses/{id}` - Atualizar despesa
- `DELETE /expenses/{id}` - Deletar despesa
- `GET /expenses/property/{property_id}` - Despesas de uma propriedade
- `GET /expenses/category/{category}` - Filtrar por categoria

**Campos principais:**
- `property_id` - Propriedade relacionada
- `description` - Descrição da despesa
- `amount` - Valor
- `category` - Categoria (maintenance, tax, utility, insurance, other)
- `expense_date` - Data da despesa
- `paid` - Se foi paga

### 8. Notificações (`/notifications`)

Sistema de notificações.

**Endpoints:**
- `GET /notifications` - Listar notificações
- `POST /notifications` - Criar notificação
- `GET /notifications/{id}` - Obter notificação
- `PUT /notifications/{id}/read` - Marcar como lida
- `DELETE /notifications/{id}` - Deletar notificação
- `GET /notifications/unread` - Notificações não lidas

### 9. Dashboard (`/dashboard`)

Estatísticas e análises.

**Endpoints:**
- `GET /dashboard/summary` - Resumo geral
- `GET /dashboard/revenue` - Receitas mensais
- `GET /dashboard/expenses` - Despesas mensais
- `GET /dashboard/properties` - Estatísticas de propriedades
- `GET /dashboard/recent-activity` - Atividades recentes

## 🔐 Autenticação

O sistema utiliza **JWT (JSON Web Tokens)** para autenticação.

### Configuração

No arquivo `.env`:
```env
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Fluxo de Autenticação

1. **Registro:** `POST /api/v1/auth/register`
2. **Login:** `POST /api/v1/auth/login` → Retorna `access_token`
3. **Requisições:** Incluir header `Authorization: Bearer {token}`

### Proteção de Rotas

Todas as rotas (exceto `/auth/register` e `/auth/login`) requerem autenticação.

**Exemplo de uso:**
```python
from app.src.auth.dependencies import get_current_active_user

@router.get("/protected")
def protected_route(current_user: User = Depends(get_current_active_user)):
    return {"message": f"Hello {current_user.username}"}
```

### Documentação Completa
- [Documentação de Autenticação](./AUTH_DOCUMENTATION.md)
- [Exemplos de Uso](./AUTH_EXAMPLES.md)

## 🗄️ Banco de Dados

### Modelo de Dados (ER Diagram)

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│  Properties │──1:N──│    Units     │──1:N──│  Contracts  │
└─────────────┘       └──────────────┘       └─────────────┘
                                                     │
                                                   1:N
                                                     │
┌─────────────┐                              ┌─────────────┐
│   Tenants   │──────────────1:N─────────────│  Payments   │
└─────────────┘                              └─────────────┘
       │                                             │
       │                                             │
     1:N                                           1:N
       │                                             │
┌─────────────┐                              ┌─────────────┐
│ Contracts   │                              │  Expenses   │
└─────────────┘                              └─────────────┘
                                                     │
                                                   N:1
                                                     │
                                              ┌─────────────┐
                                              │ Properties  │
                                              └─────────────┘
```

### Tabelas Principais

1. **users** - Usuários do sistema (autenticação)
2. **properties** - Propriedades/imóveis
3. **units** - Unidades individuais (apartamentos)
4. **tenants** - Inquilinos
5. **contracts** - Contratos de aluguel
6. **payments** - Pagamentos
7. **expenses** - Despesas
8. **notifications** - Notificações

### Migrations

O sistema utiliza Alembic para migrações. Para criar uma nova migração:

```bash
# Criar migração
alembic revision --autogenerate -m "description"

# Aplicar migrações
alembic upgrade head

# Reverter migração
alembic downgrade -1
```

## 🧪 Testes

### Estrutura de Testes

```
tests/
├── unit/                   # Testes unitários (85% cobertura)
│   ├── test_auth.py
│   ├── test_properties.py
│   ├── test_tenants.py
│   └── test_payments.py
├── integration/            # Testes de integração
│   └── test_payment_flow.py
├── parametrized/           # Testes parametrizados
│   └── test_validations.py
└── conftest.py            # Fixtures compartilhadas
```

### Executar Testes

**Localmente:**
```bash
pytest -v
pytest --cov=app --cov-report=html
```

**Com Docker:**
```bash
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

**Windows PowerShell:**
```powershell
.\run_tests.ps1
```

**Makefile:**
```bash
make test
make test-cov
make test-docker
```

### Qualidade de Código

O projeto utiliza as seguintes ferramentas:

- **Black** - Formatação de código (line-length: 100)
- **isort** - Organização de imports
- **Flake8** - Linting
- **MyPy** - Type checking
- **Pytest** - Testes + Coverage

**Executar todas as verificações:**
```bash
make lint
make format
```

## 💻 Desenvolvimento

### Configuração do Ambiente

1. **Clone o repositório**
2. **Copie o arquivo de configuração:**
   ```bash
   cp .env.example .env
   ```
3. **Inicie com Docker:**
   ```bash
   docker-compose up --build
   ```

### Convenções de Código

1. **Nomenclatura:**
   - Modelos: PascalCase (`User`, `Property`)
   - Funções/métodos: snake_case (`get_user`, `create_property`)
   - Constantes: UPPER_SNAKE_CASE (`SECRET_KEY`, `DATABASE_URL`)

2. **Estrutura de módulo:**
   ```python
   # models.py
   class Entity(Base):
       __tablename__ = "entities"
       # ...

   # schemas.py
   class EntityBase(BaseModel):
       # campos comuns

   class EntityCreate(EntityBase):
       # campos para criação

   class EntityUpdate(EntityBase):
       # campos para atualização (todos opcionais)

   class EntityResponse(EntityBase):
       id: int
       created_at: datetime
       # ...

   # repository.py
   class EntityRepository(BaseRepository[Entity, EntityCreate, EntityUpdate]):
       def custom_query(self, db: Session, param: str):
           # ...

   # controller.py
   class EntityController:
       def __init__(self, db: Session):
           self.db = db
           self.repository = EntityRepository()

       def get_entities(self, db: Session, skip: int = 0, limit: int = 100):
           return self.repository.get_multi(db, skip=skip, limit=limit)

   # router.py
   @router.get("/", response_model=List[EntityResponse])
   def list_entities(
       skip: int = 0,
       limit: int = 100,
       db: Session = Depends(get_db),
       current_user: User = Depends(get_current_active_user)
   ):
       controller = EntityController(db)
       return controller.get_entities(db, skip, limit)
   ```

3. **Type Hints:**
   - Sempre use type hints em funções e métodos
   - Use `Optional[Type]` para valores nullable
   - Use `List[Type]` ou `Sequence[Type]` para listas

4. **Documentação:**
   - Docstrings em todas as classes e funções públicas
   - Formato Google Docstring Style

### CI/CD

O projeto utiliza GitHub Actions para:

1. **Linting e Testes** (em cada push/PR)
   - Black, isort, Flake8, MyPy
   - Pytest com coverage
   - Coverage report

2. **Docker Build** (em cada push)
   - Verificação de build da imagem Docker

### Pre-commit Hooks

O projeto usa pre-commit hooks para garantir qualidade:

```bash
# Instalar hooks
pre-commit install

# Executar manualmente
pre-commit run --all-files
```

## 📊 Estatísticas do Projeto

- **Linhas de Código:** ~2000 (app/)
- **Cobertura de Testes:** 66%
- **Testes:** 99 testes (88 passando, 11 legados)
- **Módulos:** 9 módulos de negócio
- **Endpoints:** 70+ endpoints REST

## 🔗 Links Úteis

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
- **Health Check:** http://localhost:8000/health

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique a documentação específica do módulo em `/docs`
2. Execute os testes para verificar a integridade
3. Consulte os logs do Docker: `docker-compose logs -f`

---

## 📚 Documentação para Frontend

### 🎯 Documentos Essenciais

1. **[QUICK_START_FRONTEND.md](./QUICK_START_FRONTEND.md)** - ⭐ Comece aqui!
   - Guia rápido de integração
   - Configuração do Axios
   - Exemplos práticos completos
   - Componentes React prontos

2. **[CHANGELOG_FRONTEND.md](./CHANGELOG_FRONTEND.md)** - ⚠️ Mudanças Importantes
   - Breaking changes (multi-tenancy, trailing slashes)
   - Checklist de atualização
   - Guia de migração

3. **[API_REFERENCE_FRONTEND.md](./API_REFERENCE_FRONTEND.md)** - 📖 Referência Completa
   - Todos os endpoints detalhados
   - Interfaces TypeScript
   - Códigos de status HTTP
   - Exemplos de uso

4. **[UPLOAD_ENDPOINTS.md](./UPLOAD_ENDPOINTS.md)** - 📤 Upload de Arquivos
   - Endpoints de upload
   - Formatos e limitações
   - Exemplos com FormData

### ⚠️ Mudanças Recentes (19/11/2025)

**IMPORTANTE - Breaking Changes:**

1. **Multi-tenancy em Despesas:** Todos endpoints requerem autenticação JWT
2. **Trailing Slashes Obrigatórios:** URLs sem `/` perdem autenticação no redirect
3. **Novo campo:** `user_id` em Expense (preenchido automaticamente)
4. **Campo removido:** `notes` em Expense
5. **Novos filtros:** `year` e `month` em listagem de despesas

**Leia o CHANGELOG_FRONTEND.md antes de atualizar seu código!**

---

**Última atualização:** 19 de Novembro de 2025
**Versão da API:** v1
