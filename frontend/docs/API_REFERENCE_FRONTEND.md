# API Endpoints - Documentação para Frontend

**Base URL:** `http://localhost:8000/api/v1`

**Autenticação:** Todos os endpoints requerem Bearer Token no header:
```
Authorization: Bearer {token}
```

---

## 🏠 IMÓVEIS (Properties)

### Listar Imóveis
```http
GET /properties
```
**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100)
- `property_type` (string): apartment, house, commercial, studio
- `status` (string): vacant, occupied, maintenance, inactive
- `min_rent` (float)
- `max_rent` (float)
- `min_area` (float)
- `max_area` (float)

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
    "description": "Casa ampla...",
    "images": ["/uploads/properties/1/image1.jpg"],
    "is_residential": true,
    "tenant": null,
    "created_at": "2025-11-18T10:00:00",
    "updated_at": "2025-11-18T10:00:00"
  }
]
```

### Criar Imóvel
```http
POST /properties
```
**Body:**
```json
{
  "name": "Apartamento Centro",
  "address": "Rua Principal, 100",
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
  "description": "Apartamento bem localizado",
  "is_residential": true
}
```

### Buscar Imóvel por ID
```http
GET /properties/{property_id}
```

### Atualizar Imóvel
```http
PUT /properties/{property_id}
```
**Body:** Mesma estrutura do POST (todos os campos opcionais)

### Atualizar Status do Imóvel
```http
PATCH /properties/{property_id}/status?status=occupied
```

### Deletar Imóvel
```http
DELETE /properties/{property_id}
```

### Upload de Imagens
```http
POST /properties/{property_id}/upload-images
```
**Content-Type:** `multipart/form-data`
**Body:**
```
files: File[] (até 10 imagens)
```

### Deletar Imagem
```http
DELETE /properties/{property_id}/images?image_url=/uploads/properties/1/image.jpg
```

---

## 👤 INQUILINOS (Tenants)

### Listar Inquilinos
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
    "documents": [
      {
        "id": "doc123",
        "name": "CNH",
        "type": "cnh",
        "url": "/uploads/tenants/1/cnh.pdf",
        "file_type": "pdf",
        "size": 524288,
        "uploaded_at": "2025-11-18T10:00:00"
      }
    ],
    "status": "active",
    "created_at": "2025-11-18T10:00:00",
    "updated_at": "2025-11-18T10:00:00"
  }
]
```

### Criar Inquilino
```http
POST /tenants
```
**Body:**
```json
{
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
```

### Buscar Inquilino por ID
```http
GET /tenants/{tenant_id}
```

### Atualizar Inquilino
```http
PUT /tenants/{tenant_id}
```

### Deletar Inquilino
```http
DELETE /tenants/{tenant_id}
```

### Upload de Documentos
```http
POST /tenants/{tenant_id}/upload-documents?document_type=cnh
```
**Content-Type:** `multipart/form-data`
**Body:**
```
files: File[] (até 5 arquivos)
```
**document_type:** rg, cpf, cnh, comprovante_residencia, comprovante_renda, contrato, outros

### Listar Documentos
```http
GET /tenants/{tenant_id}/documents
```

### Deletar Documento
```http
DELETE /tenants/{tenant_id}/documents?document_url=/uploads/tenants/1/doc.pdf
```

---

## 📄 CONTRATOS (Contracts)

Importante: A estrutura atual não possui o campo `payment_day` na tabela; o vencimento é derivado da lógica de cálculo configurada no serviço de pagamentos (ex.: usar `due_date` explícita no momento do cálculo/registro).

### Listar Contratos

```http
GET /contracts?skip=0&limit=100&status=active&property_id=1&tenant_id=1
```

**Response (estrutura real):**

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
    "status": "active",
    "document_url": "/uploads/contracts/contract1.pdf",
    "created_at": "2025-11-18T10:00:00",
    "updated_at": "2025-11-18T10:00:00"
  }
]
```

### Criar Contrato

```http
POST /contracts
```
**Body (campos suportados):**

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
  "status": "active",
  "document_url": null
}
```

### Buscar Contrato por ID

```http
GET /contracts/{contract_id}
```

### Atualizar Contrato

```http
PUT /contracts/{contract_id}
```

### Deletar Contrato

```http
DELETE /contracts/{contract_id}
```

### Renovar Contrato

```http
PATCH /contracts/{contract_id}/renew
```
**Body:**
```json
{
  "new_end_date": "2026-12-31",
  "new_rent": 1600.00
}
```

### Atualizar Status do Contrato

```http
PATCH /contracts/{contract_id}/status
```
**Body:**
```json
{
  "status": "expired"
}
```

### Listar Contratos Ativos

```http
GET /contracts/active
```

### Listar Contratos Expirando

```http
GET /contracts/expiring?days_ahead=30
```

---

## 💳 PAGAMENTOS (Payments)

### Visão Geral

O fluxo de pagamentos agora divide-se em:

1. Preview (cálculo) – não persiste nada, apenas retorna multa/juros/total.
2. Registro – grava o pagamento aplicando a lógica automática.

Endpoints principais:

- `POST /payments/calculate` (preview)
- `POST /payments/register` (registro efetivo)
- `GET /payments` (listagem com filtros)
- `PATCH /payments/{id}/confirm` (confirmação manual de pagamento simples)


### 1. Preview de Pagamento

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
Campos:
- `contract_id` (int) – deve pertencer ao usuário autenticado
- `due_date` (string YYYY-MM-DD) – data de vencimento pretendida
- `payment_date` (string YYYY-MM-DD) – data em que será pago
- `paid_amount` (number | null) – informe valor para simular parcial; `null` apenas calcula

**Response (exemplo real):**

```json
{
  "base_amount": "2500.00",
  "fine_amount": "250.0000",
  "interest_amount": "4.166666666666666666666666666",
  "total_addition": "254.1666666666666666666666667",
  "total_expected": "2754.166666666666666666666667",
  "days_overdue": 5,
  "status": "pending",
  "paid_amount": "0",
  "remaining_amount": "2754.166666666666666666666667"
}
```
Observações:
- `fine_amount`: multa (10% do valor base) aplicada apenas se atraso.
- `interest_amount`: juros proporcionais (1% ao mês distribuído diariamente).
- `status`: pode permanecer `pending` no preview mesmo com atraso (lógica de ajuste posterior).
- `remaining_amount`: quanto faltaria se nenhum valor pago foi informado.

### 2. Registrar Pagamento

```http
POST /payments/register
```
**Body (exemplo real usado em teste atrasado 5 dias):**

```json
{
  "contract_id": 3,
  "due_date": "2025-11-23",
  "payment_date": "2025-11-28",
  "paid_amount": 2754.17,
  "payment_method": "pix",
  "description": "Pagamento novembro (atraso 5 dias)"
}
```
Campos:
- `contract_id` (int) – obrigatório.
- `due_date` (string) – vencimento que está sendo liquidado.
- `payment_date` (string) – data do efetivo pagamento.
- `paid_amount` (number) – total pago (incluindo multa/juros se atrasado).
- `payment_method` (string) – `pix|boleto|transferencia|dinheiro|cartao_credito|cartao_debito|outro`.
- `description` (string, opcional).

**Response (exemplo real):**

```json
{
  "property_id": 2,
  "tenant_id": 2,
  "contract_id": 3,
  "due_date": "2025-11-23",
  "payment_date": "2025-11-28",
  "amount": "2754.17",
  "fine_amount": "254.17",
  "total_amount": "2754.17",
  "status": "paid",
  "payment_method": "pix",
  "description": "Pagamento novembro (atraso 5 dias)",
  "id": 6,
  "created_at": "2025-11-23T14:12:43.875610",
  "updated_at": "2025-11-23T14:12:43.875614"
}
```
Notas:
- `amount` aqui reflete o valor pago final (incluindo acréscimos) – pode diferir de um modelo ideal onde haveria `base_amount` separado.
- `fine_amount` e `total_amount` confirmam valores aplicados.
- Não há `reference_month` no retorno atual (campo legado removido da resposta real).

### 3. Listar Pagamentos

```http
GET /payments?skip=0&limit=50&status=paid&contract_id=3
```
Query Parameters suportados:
- `skip` (int) – paginação.
- `limit` (int) – máximo de registros.
- `status` (`pending|paid|overdue|partial`).
- `contract_id`, `tenant_id`, `property_id` (int) – filtros.

### 4. Confirmar Pagamento Simples

```http
PATCH /payments/{payment_id}/confirm
```
**Body:**

```json
{
  "payment_date": "2025-11-28",
  "payment_method": "pix"
}
```
Uso: quando registro inicial foi criado só como pendente (sem cálculo de multa/juros) e deseja-se marcar como pago manualmente.

### 5. Pagamentos Pendentes / Atrasados

```http
GET /payments/pending
GET /payments/overdue
```

### Tipos (TypeScript)

```typescript
type PaymentStatus = 'pending' | 'paid' | 'overdue' | 'partial';
type PaymentMethod = 'pix' | 'boleto' | 'transferencia' | 'dinheiro' | 'cartao_credito' | 'cartao_debito' | 'outro';

interface PaymentPreview {
  base_amount: string;          // valor base do aluguel
  fine_amount: string;          // multa aplicada
  interest_amount: string;      // juros proporcionais
  total_addition: string;       // soma multa+juros
  total_expected: string;       // total a pagar
  days_overdue: number;
  status: PaymentStatus;
  paid_amount: string;          // informado ou '0'
  remaining_amount: string;     // diferença
}

interface PaymentRecord {
  id: number;
  contract_id: number;
  tenant_id: number;
  property_id: number;
  due_date: string;
  payment_date: string | null;
  amount: string;               // total efetivamente pago
  fine_amount: string;          // multa
  total_amount: string;         // total (redundante = amount)
  status: PaymentStatus;
  payment_method: PaymentMethod | null;
  description?: string | null;
  created_at: string;
  updated_at: string;
}
```

### Exemplo de Fluxo (Frontend)

```typescript
// 1. Calcular preview
const preview = await api.post<PaymentPreview>('/payments/calculate', {
  contract_id: 3,
  due_date: '2025-11-23',
  payment_date: '2025-11-28',
  paid_amount: null
});

// 2. Registrar pagamento usando total esperado
const registro = await api.post<PaymentRecord>('/payments/register', {
  contract_id: 3,
  due_date: '2025-11-23',
  payment_date: '2025-11-28',
  paid_amount: Number(preview.data.total_expected).toFixed(2),
  payment_method: 'pix',
  description: 'Pagamento novembro (atraso 5 dias)'
});
```

### Observações Importantes
- O `contract_id` deve pertencer ao usuário autenticado (senão 404/403).
- Diferenças de atraso: mesmo se `days_overdue > 0`, o preview pode retornar `status: pending` (ajuste futuro possível).
- Campos não presentes na resposta real (ex. `reference_month`) não devem ser usados no frontend.
- Para pagamentos parciais: enviar `paid_amount` menor que `total_expected`; status lógico poderá ser `partial` se implementado.

### Erros Comuns
| Código | Motivo | Ação |
|--------|--------|------|
| 401 | Token ausente/inválido | Refazer login |
| 403 | Contrato não pertence ao usuário | Verificar `contract_id` |
| 404 | Contrato inexistente | Validar ID antes |
| 422 | Formato inválido (datas/valores) | Corrigir payload |
| 500 | Erro interno (antes do ajuste de create) | Já corrigido na API |

### Buscar Pagamento por ID
```http
GET /payments/{payment_id}
```

### Atualizar Pagamento
```http
PUT /payments/{payment_id}
```

### Deletar Pagamento
```http
DELETE /payments/{payment_id}
```

### Confirmar Pagamento
```http
PATCH /payments/{payment_id}/confirm
```
**Body:**
```json
{
  "payment_date": "2025-11-08",
  "payment_method": "pix"
}
```

### Listar Pagamentos Pendentes
```http
GET /payments/pending
```

### Listar Pagamentos em Atraso
```http
GET /payments/overdue
```

---

## 💰 DESPESAS (Expenses)

### ⚠️ IMPORTANTE - AUTENTICAÇÃO OBRIGATÓRIA
**TODOS os endpoints de despesas requerem autenticação JWT e implementam multi-tenancy.**
- Cada usuário vê apenas suas próprias despesas
- Tentativas de acessar despesas de outros usuários retornam **403 Forbidden**

### Listar Despesas
```http
GET /api/v1/expenses/?skip=0&limit=100&property_id=1&category=manutenção&status=pending&year=2025&month=11
```

**Query Parameters:**
- `skip` (int, default: 0): Paginação - registros a pular
- `limit` (int, default: 100): Paginação - máximo de registros
- `property_id` (int, opcional): Filtrar por imóvel específico
- `category` (string, opcional): Filtrar por categoria
- `year` (int, opcional): Filtrar por ano
- `month` (int, opcional): Filtrar por mês (1-12)

**Headers:**
```
Authorization: Bearer {seu_token_jwt}
```

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
    "receipt": "/uploads/expenses/f1f8db9f-16a8-4644-9db4-875befd97f3a/nota.pdf",
    "created_at": "2025-11-15T10:00:00",
    "updated_at": "2025-11-15T15:00:00"
  }
]
```

### Criar Despesa
```http
POST /api/v1/expenses/
```

**Headers:**
```
Authorization: Bearer {seu_token_jwt}
Content-Type: application/json
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

**Campos Obrigatórios:**
- `type` (string): **"expense"** ou **"maintenance"**
- `category` (string): Categoria da despesa
- `description` (string): Descrição detalhada
- `amount` (decimal): Valor > 0
- `date` (date): Data da despesa (formato: YYYY-MM-DD)
- `property_id` (int): ID do imóvel
- `status` (string): "pending", "paid" ou "scheduled"

**Campos Opcionais:**
- `priority` (string): "low", "medium", "high" ou "urgent"
- `vendor` (string): Nome do fornecedor
- `number` (string): Telefone/contato do fornecedor
- `receipt` (string): URL do comprovante (geralmente usado pelo endpoint de upload)

**Response (201 Created):**
```json
{
  "id": "f1f8db9f-16a8-4644-9db4-875befd97f3a",
  "user_id": 1,
  "type": "maintenance",
  "category": "Manutenção",
  "description": "Conserto do encanamento",
  "amount": 350.00,
  "date": "2025-11-15",
  "property_id": 1,
  "status": "pending",
  "priority": "high",
  "vendor": "Encanador Silva",
  "number": "(61) 98765-4321",
  "receipt": null,
  "created_at": "2025-11-15T10:00:00",
  "updated_at": "2025-11-15T10:00:00"
}
```

**Nota:** O campo `user_id` é **automaticamente preenchido** a partir do token JWT. Não envie este campo no body.

### Buscar Despesa por ID
```http
GET /api/v1/expenses/{expense_id}/
```

**Headers:**
```
Authorization: Bearer {seu_token_jwt}
```

**Response (200 OK):**
```json
{
  "id": "f1f8db9f-16a8-4644-9db4-875befd97f3a",
  "user_id": 1,
  "type": "maintenance",
  "category": "Manutenção",
  "description": "Conserto do encanamento",
  "amount": 350.00,
  "date": "2025-11-15",
  "property_id": 1,
  "status": "pending",
  "priority": "high",
  "vendor": "Encanador Silva",
  "number": "(61) 98765-4321",
  "receipt": null,
  "created_at": "2025-11-15T10:00:00",
  "updated_at": "2025-11-15T10:00:00"
}
```

**Erros Possíveis:**
- **404 Not Found:** Despesa não existe
- **403 Forbidden:** Despesa pertence a outro usuário

### Atualizar Despesa
```http
PUT /api/v1/expenses/{expense_id}/
```

**Headers:**
```
Authorization: Bearer {seu_token_jwt}
Content-Type: application/json
```

**Body (todos os campos opcionais):**
```json
{
  "type": "expense",
  "status": "paid",
  "amount": 475.00,
  "priority": "medium"
}
```

**Response (200 OK):** Retorna a despesa atualizada

**Erros Possíveis:**
- **404 Not Found:** Despesa não existe
- **403 Forbidden:** Despesa pertence a outro usuário

### Deletar Despesa
```http
DELETE /api/v1/expenses/{expense_id}/
```

**Headers:**
```
Authorization: Bearer {seu_token_jwt}
```

**Response (204 No Content):** Sem corpo na resposta

**Erros Possíveis:**
- **404 Not Found:** Despesa não existe
- **403 Forbidden:** Despesa pertence a outro usuário

### Upload de Comprovante
```http
POST /api/v1/expenses/{expense_id}/upload-receipt
```

**Headers:**
```
Authorization: Bearer {seu_token_jwt}
```

**Content-Type:** `multipart/form-data`

**Body:**
```
file: File (imagem JPG/PNG ou PDF, máximo 10MB)
```

**Response (201 Created):**
```json
{
  "message": "Comprovante enviado com sucesso",
  "file_info": {
    "filename": "20251119_153045_a1b2c3d4.pdf",
    "original_filename": "nota_fiscal.pdf",
    "url": "/uploads/expenses/f1f8db9f-16a8-4644-9db4-875befd97f3a/20251119_153045_a1b2c3d4.pdf",
    "size": 287654,
    "type": "pdf"
  },
  "expense_id": "f1f8db9f-16a8-4644-9db4-875befd97f3a"
}
```

**Comportamento:**
- Se já existir um comprovante, o arquivo antigo é **substituído**
- O campo `receipt` da despesa é automaticamente atualizado

### Deletar Comprovante
```http
DELETE /api/v1/expenses/{expense_id}/receipt
```

**Headers:**
```
Authorization: Bearer {seu_token_jwt}
```

**Response (200 OK):**
```json
{
  "message": "Comprovante deletado com sucesso",
  "file_deleted": true
}
```

**Erros Possíveis:**
- **404 Not Found:** 
  - Despesa não existe
  - Nenhum comprovante encontrado para esta despesa

### Despesas Mensais por Propriedade
```http
GET /api/v1/expenses/property/{property_id}/monthly?year=2025&month=11
```

**Response:**
```json
{
  "property_id": 1,
  "year": 2025,
  "month": 11,
  "total_expenses": 1250.75,
  "count": 5,
  "expenses": [...]
}
```

### Resumo por Categoria
```http
GET /api/v1/expenses/categories/summary?property_id=1&year=2025&month=11
```

**Response:**
```json
{
  "categories": {
    "Manutenção": {
      "total": 850.00,
      "count": 3,
      "expenses": [...]
    },
    "Contas": {
      "total": 400.75,
      "count": 2,
      "expenses": [...]
    }
  }
}
```

---

## 📊 DASHBOARD

### Estatísticas Básicas
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

### Resumo Completo
```http
GET /dashboard/summary
```
**Response:**
```json
{
  "properties": {
    "total": 10,
    "active_contracts": 7
  },
  "contracts": {
    "active": 7,
    "expiring_soon": 2
  },
  "financial": {
    "monthly_revenue": 12500.00,
    "overdue_payments": 3,
    "pending_payments": 5
  }
}
```

### Gráfico de Receitas
```http
GET /dashboard/revenue-chart?months=12
```
**Response:**
```json
{
  "data": [
    {"month": "2025-01", "revenue": 10000.00},
    {"month": "2025-02", "revenue": 10500.00}
  ]
}
```

### Performance por Propriedade
```http
GET /dashboard/property-performance
```

### Atividades Recentes
```http
GET /dashboard/recent-activity?limit=10
```

---

## 🔔 NOTIFICAÇÕES (Notifications)

### Listar Notificações
```http
GET /notifications?skip=0&limit=100
```

### Criar Notificação
```http
POST /notifications
```
**Body:**
```json
{
  "title": "Pagamento Recebido",
  "message": "Pagamento do inquilino João foi confirmado",
  "type": "payment",
  "priority": "normal"
}
```

### Marcar como Lida
```http
PATCH /notifications/{notification_id}/read
```

### Deletar Notificação
```http
DELETE /notifications/{notification_id}
```

---

## 🔐 AUTENTICAÇÃO

**Auth API Base URL:** `http://localhost:8001/api/v1/auth`

### Login
```http
POST /api/v1/auth/login
```
**Body:**
```json
{
  "username": "test@test.com",
  "password": "test123"
}
```
**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### Registrar
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

### Dados do Usuário
```http
GET /api/v1/auth/me
```

---

## 📝 ESTRUTURA DE DADOS ATUALIZADA

### Expense (Despesa)

```typescript
interface Expense {
  id: string;                    // UUID
  user_id: number;               // ID do usuário proprietário (preenchido automaticamente)
  type: 'expense' | 'maintenance';  // Tipo da despesa
  category: string;              // Categoria da despesa
  description: string;           // Descrição
  amount: number;                // Valor (decimal)
  date: string;                  // Data (ISO 8601)
  property_id: number;           // ID do imóvel
  status: 'pending' | 'paid' | 'scheduled';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  vendor?: string;               // Nome do fornecedor
  number?: string;               // Telefone do fornecedor
  receipt?: string;              // URL do comprovante
  created_at: string;            // ISO 8601
  updated_at: string;            // ISO 8601
}
```

**Mudanças Importantes:**

- ✅ **NOVO CAMPO:** `user_id` - ID do usuário (extraído automaticamente do token JWT)
- ⚠️ **Multi-tenancy implementado:** Todos endpoints filtram por user_id
- ❌ **Campo removido:** `notes` - Não existe mais no schema

---

## 🚀 Exemplo de Uso (TypeScript/React)

```typescript
// config/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

// Interceptor para adicionar token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;

// services/expenseService.ts
import api from '../config/api';

export const expenseService = {
  // Listar despesas (com trailing slash!)
  async getExpenses(params?: {
    skip?: number;
    limit?: number;
    property_id?: number;
    category?: string;
    status?: string;
    year?: number;
    month?: number;
  }) {
    const { data } = await api.get('/expenses/', { params });
    return data;
  },

  // Criar despesa (com trailing slash!)
  async createExpense(expense: {
    type: 'expense' | 'maintenance';
    category: string;
    description: string;
    amount: number;
    date: string;
    property_id: number;
    status: string;
    priority?: string;
    vendor?: string;
    number?: string;  // Telefone do fornecedor
  }) {
    const { data } = await api.post('/expenses/', expense);
    return data;
  },

  // Buscar despesa por ID (com trailing slash!)
  async getExpense(expenseId: string) {
    const { data } = await api.get(`/expenses/${expenseId}/`);
    return data;
  },

  // Upload de comprovante (SEM trailing slash no final)
  async uploadReceipt(expenseId: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);
    
    const { data } = await api.post(
      `/expenses/${expenseId}/upload-receipt`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    );
    return data;
  },

  // Atualizar despesa (com trailing slash!)
  async updateExpense(expenseId: string, updates: Partial<Expense>) {
    const { data } = await api.put(`/expenses/${expenseId}/`, updates);
    return data;
  },

  // Deletar despesa (com trailing slash!)
  async deleteExpense(expenseId: string) {
    await api.delete(`/expenses/${expenseId}/`);
  },
  
  // Deletar comprovante (SEM trailing slash no final)
  async deleteReceipt(expenseId: string) {
    const { data } = await api.delete(`/expenses/${expenseId}/receipt`);
    return data;
  }
};

// Exemplo de componente React
function ExpenseForm() {
  const [file, setFile] = useState<File | null>(null);
  
  const handleSubmit = async (formData: any) => {
    try {
      // 1. Criar despesa
      const expense = await expenseService.createExpense({
        type: 'maintenance',
        category: 'Manutenção',
        description: formData.description,
        amount: parseFloat(formData.amount),
        date: formData.date,
        property_id: formData.propertyId,
        status: 'pending',
        priority: 'high',
        vendor: formData.vendor,
        number: formData.phone
      });
      
      // 2. Upload de comprovante (se houver)
      if (file) {
        await expenseService.uploadReceipt(expense.id, file);
      }
      
      alert('Despesa criada com sucesso!');
    } catch (error) {
      if (error.response?.status === 403) {
        alert('Você não tem permissão para realizar esta ação');
      } else {
        alert('Erro ao criar despesa');
      }
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Campos do formulário */}
      <input 
        type="file" 
        accept=".jpg,.jpeg,.png,.pdf"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button type="submit">Criar Despesa</button>
    </form>
  );
}
```

---

## ⚠️ Notas Importantes

### 🔒 Autenticação e Segurança

1. **TODOS os endpoints requerem autenticação** via Bearer Token (exceto login/register)
2. **Multi-tenancy implementado em Despesas:**
   - Usuários veem apenas suas próprias despesas
   - Tentativas de acessar dados de outros usuários retornam **403 Forbidden**
   - O campo `user_id` é extraído automaticamente do token JWT
3. **Não envie `user_id` no body das requisições** - será ignorado e substituído pelo valor do token

### 🌐 URLs e Trailing Slashes

⚠️ **ATENÇÃO: Trailing slashes são OBRIGATÓRIOS para endpoints autenticados!**

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
GET  /api/v1/expenses/{id} ← Causa redirect 307, perde token!
```

**Exceções (endpoints de ação não requerem `/` final):**
```
POST /api/v1/expenses/{id}/upload-receipt
DELETE /api/v1/expenses/{id}/receipt
POST /api/v1/tenants/{id}/upload-documents
DELETE /api/v1/tenants/{id}/documents
```

### 📊 Validações e Tipos de Dados

4. **Validações:** Campos obrigatórios retornam erro **422 Unprocessable Entity** se ausentes
5. **Uploads:** Usar `multipart/form-data` com tamanho máximo de **10MB**
6. **Datas:** Formato ISO 8601 (`YYYY-MM-DD` ou `YYYY-MM-DDTHH:mm:ss`)
7. **IDs:** 
   - Properties, Tenants, Contracts, Payments usam `int`
   - Expenses usa `string` (UUID v4)

### 🔄 Códigos de Status HTTP

- `200 OK` - Operação bem-sucedida
- `201 Created` - Recurso criado com sucesso
- `204 No Content` - Recurso deletado (sem corpo na resposta)
- `400 Bad Request` - Dados inválidos na requisição
- `401 Unauthorized` - Token não fornecido ou inválido
- `403 Forbidden` - Usuário sem permissão (multi-tenancy)
- `404 Not Found` - Recurso não encontrado
- `422 Unprocessable Entity` - Validação de schema falhou
