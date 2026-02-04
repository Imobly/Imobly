# API Reference

Esta seção contém a documentação completa da API REST do Imobly.

## Visão Geral

A API do Imobly é uma RESTful API construída com FastAPI que oferece endpoints para gerenciar propriedades, inquilinos, contratos e pagamentos.

### Base URLs

#### Produção (Render)
```
Backend API: https://backend-non0.onrender.com
Auth API: https://auth-api-3zxk.onrender.com
```

#### Desenvolvimento Local
```
Backend API: http://localhost:8000
Auth API: http://localhost:8001
```

!!! info "Documentação Interativa"
    - **Backend Swagger:** [backend-non0.onrender.com/docs](https://backend-non0.onrender.com/docs)
    - **Auth Swagger:** [auth-api-3zxk.onrender.com/docs](https://auth-api-3zxk.onrender.com/docs)
    - **ReDoc (Backend):** [backend-non0.onrender.com/redoc](https://backend-non0.onrender.com/redoc)
    - **ReDoc (Auth):** [auth-api-3zxk.onrender.com/redoc](https://auth-api-3zxk.onrender.com/redoc)

### Versionamento

A API usa versionamento por URL. A versão atual é `v1`.

### Formato de Resposta

Todas as respostas da API são em formato JSON:

    {
      "success": true,
      "data": {},
      "message": "Operação realizada com sucesso"
    }

## Autenticação

A API usa autenticação JWT (JSON Web Token). Para acessar endpoints protegidos, inclua o token no header:

```
Authorization: Bearer <token>
```

!!! warning "Multi-Tenancy"
    Todos os endpoints implementam **multi-tenancy**. Cada usuário vê apenas seus próprios dados. Tentativas de acessar recursos de outros usuários retornam **403 Forbidden**.

### Endpoints de Autenticação

**Auth API:** `https://auth-api-3zxk.onrender.com/api/v1/auth`

#### Login
```http
POST /api/v1/auth/login
```
**Body:**
```json
{
  "username": "user@email.com",
  "password": "senha123"
}
```
**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### Registrar
```http
POST /api/v1/auth/register
```
**Body:**
```json
{
  "email": "user@email.com",
  "password": "senha123",
  "name": "Nome do Usuário"
}
```

#### Dados do Usuário
```http
GET /api/v1/auth/me
```
Retorna informações do usuário autenticado.

## Recursos Principais

### 🏠 Properties (Propriedades)

Gerenciamento de propriedades imobiliárias.

#### Listar Propriedades
```http
GET /properties?skip=0&limit=100&property_type=apartment&status=vacant
```

**Query Parameters:**
- `skip` (int): Paginação - registros a pular
- `limit` (int): Máximo de registros (default: 100)
- `property_type`: apartment, house, commercial, studio
- `status`: vacant, occupied, maintenance, inactive
- `min_rent`, `max_rent` (float): Filtro de valor
- `min_area`, `max_area` (float): Filtro de área

**Response:**
```json
[
  {
    "id": 1,
    "name": "Casa QS 12",
    "address": "Quadra 201, 1204",
    "neighborhood": "Samambaia Norte",
    "city": "Brasília",
    "state": "DF",
    "zip_code": "72311-312",
    "type": "house",
    "area": 120.5,
    "bedrooms": 3,
    "bathrooms": 2,
    "parking_spaces": 2,
    "rent": 1500.00,
    "status": "vacant",
    "is_residential": true,
    "tenant_id": null
  }
]
```

#### Criar Propriedade
```http
POST /properties
```

#### Atualizar Propriedade
```http
PUT /properties/{property_id}
```

#### Upload de Imagens
```http
POST /properties/{property_id}/upload-images
```
**Content-Type:** multipart/form-data (até 10 imagens)

### 👤 Tenants (Inquilinos)

Gerenciamento de inquilinos.

#### Listar Inquilinos
```http
GET /tenants?skip=0&limit=100
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "João Silva",
    "email": "joao@email.com",
    "phone": "(61) 99999-9999",
    "cpf_cnpj": "123.456.789-00",
    "birth_date": "1990-01-15",
    "profession": "Engenheiro",
    "emergency_contact": {
      "name": "Maria Silva",
      "phone": "(61) 88888-8888",
      "relationship": "Esposa"
    },
    "status": "active"
  }
]
```

#### Upload de Documentos
```http
POST /tenants/{tenant_id}/upload-documents?document_type=cnh
```
**Content-Type:** multipart/form-data (até 5 arquivos)

**Tipos de Documento:** rg, cpf, cnh, comprovante_residencia, comprovante_renda, contrato, outros

### 📝 Contracts (Contratos)

Gerenciamento de contratos de locação.

#### Listar Contratos
```http
GET /contracts?skip=0&limit=100&status=active&property_id=1
```

**Response:**
```json
[
  {
    "id": 1,
    "property_id": 1,
    "tenant_id": 1,
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "rent": 1500.00,
    "deposit": 3000.00,
    "interest_rate": 2.00,
    "fine_rate": 10.00,
    "status": "active"
  }
]
```

#### Criar Contrato
```http
POST /contracts
```
**Body:**
```json
{
  "property_id": 1,
  "tenant_id": 1,
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "rent": 1500.00,
  "deposit": 3000.00,
  "interest_rate": 2.00,
  "fine_rate": 10.00,
  "status": "active"
}
```

#### Renovar Contrato
```http
PATCH /contracts/{contract_id}/renew
```

#### Contratos Expirando
```http
GET /contracts/expiring?days_ahead=30
```

### 💰 Payments (Pagamentos)

Gerenciamento de pagamentos com cálculo automático de multas e juros.

!!! info "Fluxo de Pagamentos"
    1. **Preview** (`/payments/calculate`) - Calcula multa/juros sem persistir
    2. **Registro** (`/payments/register`) - Grava o pagamento com cálculo automático

#### Preview de Pagamento
```http
POST /payments/calculate
```
**Body:**
```json
{
  "contract_id": 3,
  "due_date": "2025-11-23",
  "payment_date": "2025-11-28",
  "paid_amount": null
}
```

**Response:**
```json
{
  "base_amount": "2500.00",
  "fine_amount": "250.00",
  "interest_amount": "4.17",
  "total_addition": "254.17",
  "total_expected": "2754.17",
  "days_overdue": 5,
  "status": "pending"
}
```

#### Registrar Pagamento
```http
POST /payments/register
```
**Body:**
```json
{
  "contract_id": 3,
  "due_date": "2025-11-23",
  "payment_date": "2025-11-28",
  "paid_amount": 2754.17,
  "payment_method": "pix",
  "description": "Pagamento novembro"
}
```

**Payment Methods:** pix, boleto, transferencia, dinheiro, cartao_credito, cartao_debito, outro

#### Listar Pagamentos
```http
GET /payments?skip=0&limit=50&status=paid&contract_id=3
```

#### Pagamentos Pendentes/Atrasados
```http
GET /payments/pending
GET /payments/overdue
```

---

### 💰 Expenses (Despesas)

Gerenciamento de despesas com multi-tenancy implementado.

!!! warning "Autenticação Obrigatória"
    Todos os endpoints de despesas implementam **multi-tenancy**. Usuários veem apenas suas próprias despesas. O campo `user_id` é extraído automaticamente do token JWT.

!!! danger "Trailing Slash Obrigatório"
    URLs autenticadas **devem** terminar com `/` para evitar perda do token na autenticação:
    - ✅ `/api/v1/expenses/`
    - ❌ `/api/v1/expenses` (causa redirect 307, perde token)

#### Listar Despesas
```http
GET /api/v1/expenses/?skip=0&limit=100&property_id=1&status=pending
```

**Query Parameters:**
- `skip` (int): Paginação
- `limit` (int): Máximo de registros (default: 100)
- `property_id` (int): Filtrar por imóvel
- `category` (string): Filtrar por categoria
- `status`: pending, paid, scheduled
- `year`, `month` (int): Filtros temporais

**Response:**
```json
[
  {
    "id": "f1f8db9f-16a8-4644-9db4-875befd97f3a",
    "user_id": 1,
    "type": "maintenance",
    "category": "Manutenção",
    "description": "Conserto do encanamento",
    "amount": 350.00,
    "date": "2025-11-15",
    "property_id": 1,
    "status": "paid",
    "priority": "high",
    "vendor": "Encanador Silva",
    "number": "(61) 98765-4321",
    "receipt": "/uploads/expenses/..../nota.pdf"
  }
]
```

#### Criar Despesa
```http
POST /api/v1/expenses/
```
**Body:**
```json
{
  "type": "maintenance",
  "category": "Manutenção",
  "description": "Conserto do encanamento",
  "amount": 350.00,
  "date": "2025-11-15",
  "property_id": 1,
  "status": "pending",
  "priority": "high",
  "vendor": "Encanador Silva",
  "number": "(61) 98765-4321"
}
```

**Tipos:** expense, maintenance  
**Status:** pending, paid, scheduled  
**Prioridades:** low, medium, high, urgent

#### Upload de Comprovante
```http
POST /api/v1/expenses/{expense_id}/upload-receipt
```
**Content-Type:** multipart/form-data (máximo 10MB)

#### Deletar Comprovante
```http
DELETE /api/v1/expenses/{expense_id}/receipt
```

---

### 📊 Dashboard

Estatísticas e resumos do sistema.

#### Estatísticas Básicas
```http
GET /dashboard/stats
```

**Response:**
```json
{
  "total_properties": 10,
  "total_tenants": 8,
  "total_contracts": 7,
  "monthly_revenue": 12500.00
}
```

#### Resumo Completo
```http
GET /dashboard/summary
```

#### Gráfico de Receitas
```http
GET /dashboard/revenue-chart?months=12
```

---

### 🔔 Notifications (Notificações)

Sistema de notificações automáticas.

#### Listar Notificações
```http
GET /notifications?skip=0&limit=100
```

#### Marcar como Lida
```http
PATCH /notifications/{notification_id}/read
```

## Códigos de Status

| Código | Descrição |
|--------|-----------|
| 200 | OK - Requisição bem-sucedida |
| 201 | Created - Recurso criado com sucesso |
| 400 | Bad Request - Dados inválidos |
| 401 | Unauthorized - Token inválido ou ausente |
| 403 | Forbidden - Sem permissão para acessar |
| 404 | Not Found - Recurso não encontrado |
| 422 | Validation Error - Erro de validação |
| 500 | Internal Server Error - Erro interno |

## Paginação

Para endpoints que retornam listas, use os parâmetros:

- `page` - Número da página (padrão: 1)
- `limit` - Itens por página (padrão: 10, máximo: 100)

Exemplo:

    GET /properties?page=2&limit=20

## Filtros e Busca

Muitos endpoints suportam filtros via query parameters:

- `search` - Busca por texto
- `status` - Filtrar por status
- `created_at_start` - Data de início
- `created_at_end` - Data de fim

Exemplo:

    GET /properties?search=apartamento&status=active

## Rate Limiting

A API tem limite de taxa de 100 requisições por minuto por IP.

Headers de resposta incluem:

- `X-RateLimit-Limit` - Limite total
- `X-RateLimit-Remaining` - Requisições restantes
- `X-RateLimit-Reset` - Timestamp do reset

## ⚠️ Notas Importantes

### 🌐 URLs e Trailing Slashes

!!! danger "Trailing Slashes Obrigatórios"
    **Endpoints autenticados requerem `/` no final da URL!**
    
    FastAPI redireciona URLs sem trailing slash (307 Temporary Redirect), mas o redirect **perde o header Authorization**.

**✅ URLs CORRETAS (com `/`):**
```
GET  /api/v1/expenses/
POST /api/v1/expenses/
GET  /api/v1/expenses/{id}/
PUT  /api/v1/expenses/{id}/
DELETE /api/v1/expenses/{id}/
```

**❌ URLs INCORRETAS (sem `/`):**
```
GET  /api/v1/expenses     ← Causa redirect 307, perde token!
POST /api/v1/expenses     ← Causa redirect 307, perde token!
```

**Exceções (endpoints de ação não requerem `/` final):**
```
POST /api/v1/expenses/{id}/upload-receipt
DELETE /api/v1/expenses/{id}/receipt
POST /api/v1/tenants/{id}/upload-documents
POST /api/v1/properties/{id}/upload-images
```

### 🔒 Multi-Tenancy

Todos os endpoints implementam **isolamento de dados por usuário**:

- O campo `user_id` é extraído automaticamente do token JWT
- **Não envie** `user_id` no body das requisições
- Tentativas de acessar dados de outros usuários retornam **403 Forbidden**
- Cada usuário vê apenas seus próprios:
  - Propriedades
  - Inquilinos
  - Contratos
  - Pagamentos
  - Despesas
  - Notificações

### 📊 Validações

- **Campos obrigatórios:** Erro 422 se ausentes
- **Uploads:** Máximo 10MB, formatos: JPG, PNG, PDF
- **Datas:** Formato ISO 8601 (`YYYY-MM-DD` ou `YYYY-MM-DDTHH:mm:ss`)
- **IDs:** 
  - Properties, Tenants, Contracts, Payments: `int`
  - Expenses: `string` (UUID v4)

### 🔄 Erros Comuns

| Código | Motivo | Solução |
|--------|--------|---------|
| 401 | Token ausente/inválido | Refazer login |
| 403 | Recurso de outro usuário | Verificar permissões |
| 404 | Recurso não encontrado | Validar ID |
| 422 | Validação falhou | Corrigir payload |
| 307 | Redirect (trailing slash) | Adicionar `/` ao final |

## Exemplos de Uso

### Criar uma Propriedade

**Requisição:**

```http
POST /api/v1/properties
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "Apartamento Centro",
  "address": "Rua das Flores, 123",
  "neighborhood": "Centro",
  "city": "Brasília",
  "state": "DF",
  "zip_code": "70000-000",
  "type": "apartment",
  "area": 85.5,
  "bedrooms": 2,
  "bathrooms": 1,
  "parking_spaces": 1,
  "rent": 1200.00,
  "status": "vacant",
  "is_residential": true
}
```

**Resposta:**

```json
{
  "id": 1,
  "name": "Apartamento Centro",
  "address": "Rua das Flores, 123",
  "neighborhood": "Centro",
  "city": "Brasília",
  "state": "DF",
  "type": "apartment",
  "rent": 1200.00,
  "status": "vacant",
  "created_at": "2025-12-01T10:00:00Z"
}
```

### Registrar Pagamento com Atraso

**1. Calcular Preview:**

```http
POST /api/v1/payments/calculate
Authorization: Bearer <token>

{
  "contract_id": 3,
  "due_date": "2025-11-23",
  "payment_date": "2025-11-28",
  "paid_amount": null
}
```

**Resposta:**

```json
{
  "base_amount": "2500.00",
  "fine_amount": "250.00",
  "interest_amount": "4.17",
  "total_expected": "2754.17",
  "days_overdue": 5,
  "status": "pending"
}
```

**2. Registrar Pagamento:**

```http
POST /api/v1/payments/register
Authorization: Bearer <token>

{
  "contract_id": 3,
  "due_date": "2025-11-23",
  "payment_date": "2025-11-28",
  "paid_amount": 2754.17,
  "payment_method": "pix",
  "description": "Pagamento novembro (atraso 5 dias)"
}
```

### Criar Despesa com Upload

**1. Criar Despesa:**

```http
POST /api/v1/expenses/
Content-Type: application/json
Authorization: Bearer <token>

{
  "type": "maintenance",
  "category": "Manutenção",
  "description": "Conserto do encanamento",
  "amount": 350.00,
  "date": "2025-11-15",
  "property_id": 1,
  "status": "pending",
  "priority": "high",
  "vendor": "Encanador Silva",
  "number": "(61) 98765-4321"
}
```

**2. Upload de Comprovante:**

```http
POST /api/v1/expenses/{expense_id}/upload-receipt
Content-Type: multipart/form-data
Authorization: Bearer <token>

file: [arquivo.pdf]
```

### TypeScript/React

```typescript
import axios from 'axios';

// Configuração do cliente
const api = axios.create({
  baseURL: 'https://backend-non0.onrender.com/api/v1',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Exemplo: Listar despesas
const getExpenses = async (propertyId?: number) => {
  const { data } = await api.get('/expenses/', {
    params: { property_id: propertyId }
  });
  return data;
};

// Exemplo: Calcular e registrar pagamento
const processPayment = async (contractId: number, dueDate: string) => {
  // 1. Preview
  const preview = await api.post('/payments/calculate', {
    contract_id: contractId,
    due_date: dueDate,
    payment_date: new Date().toISOString().split('T')[0],
    paid_amount: null
  });
  
  // 2. Confirmar com usuário e registrar
  const payment = await api.post('/payments/register', {
    contract_id: contractId,
    due_date: dueDate,
    payment_date: new Date().toISOString().split('T')[0],
    paid_amount: parseFloat(preview.data.total_expected),
    payment_method: 'pix'
  });
  
  return payment.data;
};
```

## Suporte

Para dúvidas sobre a API:

- **Documentação Interativa (Swagger):** 
  - Backend: [backend-non0.onrender.com/docs](https://backend-non0.onrender.com/docs)
  - Auth: [auth-api-3zxk.onrender.com/docs](https://auth-api-3zxk.onrender.com/docs)
- **Email:** devcostta@gmail.com
- **GitHub Issues:** [Reportar Bug](https://github.com/Imobly/Documentation/issues)

!!! tip "Documentação Completa"
    A documentação completa com todas as informações detalhadas está disponível no arquivo [`API_REFERENCE_FRONTEND.md`](https://github.com/Imobly/Documentation/blob/main/API_REFERENCE_FRONTEND.md)