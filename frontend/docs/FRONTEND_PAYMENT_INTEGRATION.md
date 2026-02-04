# 🚀 Guia de Integração - Sistema de Pagamentos (Frontend)

## 📍 Informações Básicas

**Base URL:** `http://localhost:8000`  
**Prefixo da API:** `/api/v1`  
**Rota de Pagamentos:** `/api/v1/payments`

---

## 🔐 Autenticação

Todos os endpoints requerem autenticação via JWT token:

```typescript
// Configuração do Axios
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptor para adicionar token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

---

## 📋 ENDPOINT 1: Listar Pagamentos

### GET `/api/v1/payments/`

Lista todos os pagamentos do usuário autenticado com filtros opcionais.

### URL Completa
```
http://localhost:8000/api/v1/payments/
```

### Parâmetros de Query (Opcionais)

| Parâmetro | Tipo | Descrição | Exemplo |
|-----------|------|-----------|---------|
| `skip` | number | Paginação - quantidade a pular | `0` |
| `limit` | number | Quantidade máxima de resultados | `100` |
| `status` | string | Filtrar por status | `pending`, `paid`, `overdue`, `partial` |
| `contract_id` | number | Filtrar por contrato | `1` |
| `tenant_id` | number | Filtrar por inquilino | `5` |
| `property_id` | number | Filtrar por propriedade | `10` |

### Exemplos de Chamada

```typescript
// 1. Listar todos os pagamentos
const response = await api.get('/payments/');

// 2. Listar pagamentos atrasados
const response = await api.get('/payments/', {
  params: { status: 'overdue' }
});

// 3. Listar pagamentos de um contrato específico
const response = await api.get('/payments/', {
  params: { contract_id: 1 }
});

// 4. Paginação (20 por página)
const response = await api.get('/payments/', {
  params: { skip: 0, limit: 20 }
});

// 5. Combinar filtros
const response = await api.get('/payments/', {
  params: {
    status: 'pending',
    property_id: 10,
    limit: 50
  }
});
```

### Resposta de Sucesso (200 OK)

```json
[
  {
    "id": 3,
    "user_id": 1,
    "property_id": 1,
    "tenant_id": 1,
    "contract_id": 4,
    "amount": 1500.00,
    "due_date": "2025-11-22",
    "payment_date": "2025-11-22",
    "paid_amount": 1500.00,
    "fine_amount": 0.00,
    "interest_amount": 0.00,
    "total_amount": 1500.00,
    "status": "paid",
    "payment_method": "pix",
    "description": "Pagamento de Novembro 2025",
    "reference_month": "2025-11-01",
    "created_at": "2025-11-22T15:30:00",
    "updated_at": "2025-11-22T15:30:00"
  },
  {
    "id": 5,
    "user_id": 1,
    "property_id": 1,
    "tenant_id": 1,
    "contract_id": 4,
    "amount": 1500.00,
    "due_date": "2025-11-25",
    "payment_date": null,
    "paid_amount": 0.00,
    "fine_amount": 0.00,
    "interest_amount": 0.00,
    "total_amount": 1500.00,
    "status": "pending",
    "payment_method": null,
    "description": "Pagamento teste - vence em 3 dias",
    "reference_month": "2025-11-01",
    "created_at": "2025-11-22T16:00:00",
    "updated_at": "2025-11-22T16:00:00"
  }
]
```

### Tipos TypeScript

```typescript
// Interface do Payment
interface Payment {
  id: number;
  user_id: number;
  property_id: number;
  tenant_id: number;
  contract_id: number;
  amount: number;              // Valor base do aluguel
  due_date: string;            // Data de vencimento (YYYY-MM-DD)
  payment_date: string | null; // Data do pagamento (YYYY-MM-DD)
  paid_amount: number;         // Valor pago
  fine_amount: number;         // Multa calculada
  interest_amount: number;     // Juros calculados
  total_amount: number;        // Total (amount + fine + interest)
  status: PaymentStatus;       // Status do pagamento
  payment_method: PaymentMethod | null; // Método de pagamento
  description: string | null;  // Descrição/observação
  reference_month: string;     // Mês de referência (YYYY-MM-01)
  created_at: string;          // ISO 8601 timestamp
  updated_at: string;          // ISO 8601 timestamp
}

// Status possíveis
type PaymentStatus = 'pending' | 'paid' | 'overdue' | 'partial';

// Métodos de pagamento
type PaymentMethod = 
  | 'pix' 
  | 'boleto' 
  | 'transferencia' 
  | 'dinheiro' 
  | 'cartao_credito' 
  | 'cartao_debito' 
  | 'outro';

// Função de listagem
async function listarPagamentos(filtros?: {
  status?: PaymentStatus;
  contract_id?: number;
  tenant_id?: number;
  property_id?: number;
  skip?: number;
  limit?: number;
}): Promise<Payment[]> {
  const { data } = await api.get<Payment[]>('/payments/', {
    params: filtros
  });
  return data;
}
```

---

## 💰 ENDPOINT 2: Registrar Pagamento

### POST `/api/v1/payments/register`

Registra um novo pagamento com cálculo automático de multa e juros.

### URL Completa
```
http://localhost:8000/api/v1/payments/register
```

### Body (Request)

```json
{
  "contract_id": 1,
  "due_date": "2025-11-22",
  "payment_date": "2025-11-28",
  "paid_amount": 1653.00,
  "payment_method": "pix",
  "description": "Pagamento referente a Novembro/2025"
}
```

### Campos do Body

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `contract_id` | number | ✅ **SIM** | ID do contrato do inquilino |
| `due_date` | string | ✅ **SIM** | Data de vencimento (formato: `YYYY-MM-DD`) |
| `payment_date` | string | ✅ **SIM** | Data em que o pagamento foi feito (formato: `YYYY-MM-DD`) |
| `paid_amount` | number | ✅ **SIM** | Valor que foi pago pelo inquilino (ex: `1653.00`) |
| `payment_method` | string | ❌ Não | Método usado: `pix`, `boleto`, `transferencia`, `dinheiro`, `cartao_credito`, `cartao_debito`, `outro` |
| `description` | string | ❌ Não | Descrição ou observação sobre o pagamento |

### Exemplo de Chamada

```typescript
// Registrar pagamento
async function registrarPagamento() {
  try {
    const response = await api.post('/payments/register', {
      contract_id: 4,
      due_date: '2025-11-22',
      payment_date: '2025-11-28',
      paid_amount: 1653.00,
      payment_method: 'pix',
      description: 'Pagamento Novembro/2025'
    });

    console.log('Pagamento registrado:', response.data);
    return response.data;
  } catch (error) {
    console.error('Erro ao registrar:', error.response?.data);
    throw error;
  }
}
```

### Resposta de Sucesso (201 Created)

```json
{
  "id": 42,
  "user_id": 1,
  "property_id": 1,
  "tenant_id": 1,
  "contract_id": 4,
  "amount": 1500.00,
  "due_date": "2025-11-22",
  "payment_date": "2025-11-28",
  "paid_amount": 1653.00,
  "fine_amount": 150.00,
  "interest_amount": 3.00,
  "total_amount": 1653.00,
  "status": "paid",
  "payment_method": "pix",
  "description": "Pagamento Novembro/2025",
  "reference_month": "2025-11-01",
  "created_at": "2025-11-28T14:30:00",
  "updated_at": "2025-11-28T14:30:00"
}
```

### Tipos TypeScript

```typescript
// Request body
interface RegisterPaymentRequest {
  contract_id: number;
  due_date: string;        // Formato: "YYYY-MM-DD"
  payment_date: string;    // Formato: "YYYY-MM-DD"
  paid_amount: number;     // Decimal com até 2 casas: 1653.00
  payment_method?: PaymentMethod;
  description?: string;
}

// Response
interface RegisterPaymentResponse {
  id: number;
  user_id: number;
  property_id: number;
  tenant_id: number;
  contract_id: number;
  amount: number;
  due_date: string;
  payment_date: string;
  paid_amount: number;
  fine_amount: number;      // Calculado automaticamente
  interest_amount: number;  // Calculado automaticamente
  total_amount: number;     // Calculado automaticamente
  status: PaymentStatus;    // Determinado automaticamente
  payment_method: PaymentMethod | null;
  description: string | null;
  reference_month: string;
  created_at: string;
  updated_at: string;
}

// Função completa
async function registrarPagamento(
  dados: RegisterPaymentRequest
): Promise<RegisterPaymentResponse> {
  const { data } = await api.post<RegisterPaymentResponse>(
    '/payments/register',
    dados
  );
  return data;
}

// Uso
const novoPagamento = await registrarPagamento({
  contract_id: 4,
  due_date: '2025-11-22',
  payment_date: '2025-11-28',
  paid_amount: 1653.00,
  payment_method: 'pix',
  description: 'Pagamento Novembro/2025'
});
```

---

## 🧮 ENDPOINT 3: Calcular Valores (Preview)

### POST `/api/v1/payments/calculate`

Calcula multa, juros e total **antes** de registrar. Use para mostrar preview.

### URL Completa
```
http://localhost:8000/api/v1/payments/calculate
```

### Body (Request)

```json
{
  "contract_id": 1,
  "due_date": "2025-11-22",
  "payment_date": "2025-11-28",
  "paid_amount": null
}
```

### Campos do Body

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `contract_id` | number | ✅ **SIM** | ID do contrato |
| `due_date` | string | ✅ **SIM** | Data de vencimento (`YYYY-MM-DD`) |
| `payment_date` | string | ✅ **SIM** | Data do pagamento (`YYYY-MM-DD`) |
| `paid_amount` | number ou null | ❌ Não | Valor pago (use `null` para apenas simular) |

### Exemplo de Chamada

```typescript
// Calcular valores ao selecionar data
async function calcularPreview(
  contratoId: number,
  dataVencimento: string,
  dataPagamento: string
) {
  const { data } = await api.post('/payments/calculate', {
    contract_id: contratoId,
    due_date: dataVencimento,
    payment_date: dataPagamento,
    paid_amount: null  // null = apenas simular
  });

  return data;
}

// Uso
const preview = await calcularPreview(4, '2025-11-22', '2025-11-28');
console.log(`Total a pagar: R$ ${preview.total_expected}`);
```

### Resposta de Sucesso (200 OK)

```json
{
  "base_amount": 1500.00,
  "fine_amount": 150.00,
  "interest_amount": 3.00,
  "total_expected": 1653.00,
  "days_overdue": 6,
  "status": "overdue",
  "paid_amount": 0.00,
  "remaining_amount": 1653.00
}
```

### Tipos TypeScript

```typescript
// Request
interface CalculatePaymentRequest {
  contract_id: number;
  due_date: string;
  payment_date: string;
  paid_amount?: number | null;
}

// Response
interface CalculatePaymentResponse {
  base_amount: number;       // Valor do aluguel
  fine_amount: number;       // Multa (10% se atrasado)
  interest_amount: number;   // Juros proporcionais
  total_expected: number;    // Total a pagar
  days_overdue: number;      // Dias de atraso
  status: PaymentStatus;     // Status calculado
  paid_amount: number;       // Valor pago (ou 0)
  remaining_amount: number;  // Valor restante
}

// Função
async function calcularPagamento(
  dados: CalculatePaymentRequest
): Promise<CalculatePaymentResponse> {
  const { data } = await api.post<CalculatePaymentResponse>(
    '/payments/calculate',
    dados
  );
  return data;
}
```

---

## 🎯 Fluxo Completo de Registro

### Passo a Passo

```typescript
import { useState } from 'react';
import api from '@/services/api';

function RegistrarPagamentoForm() {
  const [preview, setPreview] = useState<CalculatePaymentResponse | null>(null);
  const [loading, setLoading] = useState(false);

  // 1. Ao selecionar data de pagamento, calcular preview
  async function handleDataChange(dataPagamento: string) {
    setLoading(true);
    try {
      const resultado = await api.post('/payments/calculate', {
        contract_id: contratoSelecionado.id,
        due_date: contratoSelecionado.payment_day, // Ex: "2025-11-22"
        payment_date: dataPagamento,
        paid_amount: null
      });
      
      setPreview(resultado.data);
    } catch (error) {
      console.error('Erro ao calcular:', error);
      toast.error('Erro ao calcular valores');
    } finally {
      setLoading(false);
    }
  }

  // 2. Ao confirmar, registrar pagamento
  async function handleConfirmar() {
    if (!preview) return;

    setLoading(true);
    try {
      const resultado = await api.post('/payments/register', {
        contract_id: contratoSelecionado.id,
        due_date: contratoSelecionado.payment_day,
        payment_date: dataSelecionada,
        paid_amount: preview.total_expected,
        payment_method: metodoSelecionado,
        description: `Pagamento ${mesNome}/2025`
      });

      toast.success('Pagamento registrado com sucesso!');
      navigate('/pagamentos');
    } catch (error) {
      console.error('Erro ao registrar:', error);
      toast.error('Erro ao registrar pagamento');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Registrar Pagamento</h2>
      
      {/* Campo de data */}
      <input
        type="date"
        onChange={(e) => handleDataChange(e.target.value)}
        disabled={loading}
      />

      {/* Preview dos valores */}
      {preview && (
        <div className="preview-box">
          <h3>Valores Calculados:</h3>
          <p>Valor do Aluguel: R$ {preview.base_amount.toFixed(2)}</p>
          
          {preview.fine_amount > 0 && (
            <p className="text-red-600">
              Multa (10%): R$ {preview.fine_amount.toFixed(2)}
            </p>
          )}
          
          {preview.interest_amount > 0 && (
            <p className="text-orange-600">
              Juros ({preview.days_overdue} dias): R$ {preview.interest_amount.toFixed(2)}
            </p>
          )}
          
          <hr />
          <p className="font-bold text-lg">
            TOTAL A PAGAR: R$ {preview.total_expected.toFixed(2)}
          </p>
          
          {preview.days_overdue > 0 && (
            <p className="text-red-600">
              ⚠️ Pagamento com {preview.days_overdue} dias de atraso
            </p>
          )}
        </div>
      )}

      {/* Botão de confirmar */}
      <button
        onClick={handleConfirmar}
        disabled={!preview || loading}
      >
        {loading ? 'Processando...' : 'Confirmar Pagamento'}
      </button>
    </div>
  );
}
```

---

## ⚠️ Tratamento de Erros

### Erros Comuns

```typescript
async function handleApiError(error: any) {
  if (error.response) {
    const status = error.response.status;
    const detail = error.response.data?.detail;

    switch (status) {
      case 401:
        toast.error('Sessão expirada. Faça login novamente.');
        // Redirecionar para login
        navigate('/login');
        break;

      case 403:
        toast.error('Você não tem permissão para acessar este recurso.');
        break;

      case 404:
        toast.error('Contrato não encontrado.');
        break;

      case 422:
        // Erro de validação
        if (Array.isArray(detail)) {
          detail.forEach((err) => {
            const field = err.loc[err.loc.length - 1];
            toast.error(`Campo ${field}: ${err.msg}`);
          });
        } else {
          toast.error(detail || 'Dados inválidos.');
        }
        break;

      case 500:
        toast.error('Erro no servidor. Tente novamente mais tarde.');
        break;

      default:
        toast.error('Erro ao processar requisição.');
    }
  } else if (error.request) {
    toast.error('Servidor não respondeu. Verifique sua conexão.');
  } else {
    toast.error('Erro ao configurar requisição.');
  }
}

// Uso
try {
  await api.post('/payments/register', dados);
} catch (error) {
  handleApiError(error);
}
```

### Validações Importantes

```typescript
// Validar dados antes de enviar
function validarDadosPagamento(dados: RegisterPaymentRequest): boolean {
  // Contract ID obrigatório
  if (!dados.contract_id || dados.contract_id <= 0) {
    toast.error('Selecione um contrato válido');
    return false;
  }

  // Datas obrigatórias
  if (!dados.due_date || !dados.payment_date) {
    toast.error('Datas são obrigatórias');
    return false;
  }

  // Formato de data (YYYY-MM-DD)
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
  if (!dateRegex.test(dados.due_date) || !dateRegex.test(dados.payment_date)) {
    toast.error('Formato de data inválido. Use YYYY-MM-DD');
    return false;
  }

  // Valor pago obrigatório e positivo
  if (!dados.paid_amount || dados.paid_amount <= 0) {
    toast.error('Valor pago deve ser maior que zero');
    return false;
  }

  return true;
}

// Usar antes de registrar
if (validarDadosPagamento(dadosFormulario)) {
  await registrarPagamento(dadosFormulario);
}
```

---

## 📊 Outros Endpoints Úteis

### Buscar Pagamento por ID
```typescript
// GET /api/v1/payments/{id}
const { data } = await api.get<Payment>(`/payments/${paymentId}`);
```

### Atualizar Pagamento
```typescript
// PUT /api/v1/payments/{id}
const { data } = await api.put<Payment>(`/payments/${paymentId}`, {
  payment_date: '2025-11-30',
  paid_amount: 1653.00,
  payment_method: 'pix'
});
```

### Deletar Pagamento
```typescript
// DELETE /api/v1/payments/{id}
await api.delete(`/payments/${paymentId}`);
```

### Listar Apenas Pendentes
```typescript
// GET /api/v1/payments/pending
const { data } = await api.get<Payment[]>('/payments/pending');
```

### Listar Apenas Atrasados
```typescript
// GET /api/v1/payments/overdue
const { data } = await api.get<Payment[]>('/payments/overdue');
```

---

## 🎨 Componente de Status

```tsx
interface StatusBadgeProps {
  status: PaymentStatus;
}

function StatusBadge({ status }: StatusBadgeProps) {
  const config = {
    pending: {
      bg: 'bg-yellow-100',
      text: 'text-yellow-800',
      border: 'border-yellow-300',
      icon: '⏳',
      label: 'Pendente'
    },
    paid: {
      bg: 'bg-green-100',
      text: 'text-green-800',
      border: 'border-green-300',
      icon: '✅',
      label: 'Pago'
    },
    overdue: {
      bg: 'bg-red-100',
      text: 'text-red-800',
      border: 'border-red-300',
      icon: '⚠️',
      label: 'Atrasado'
    },
    partial: {
      bg: 'bg-orange-100',
      text: 'text-orange-800',
      border: 'border-orange-300',
      icon: '⚡',
      label: 'Parcial'
    }
  };

  const { bg, text, border, icon, label } = config[status];

  return (
    <span className={`px-3 py-1 rounded-full border ${bg} ${text} ${border}`}>
      {icon} {label}
    </span>
  );
}
```

---

## ✅ Checklist de Integração

- [ ] Configurar Axios com base URL e interceptor de autenticação
- [ ] Criar interfaces TypeScript para Payment e requests
- [ ] Implementar função de listar pagamentos com filtros
- [ ] Implementar função de calcular preview
- [ ] Implementar função de registrar pagamento
- [ ] Criar componente de status badge
- [ ] Criar formulário de registro com preview
- [ ] Implementar tratamento de erros
- [ ] Adicionar validações de campos
- [ ] Testar fluxo completo (calcular → preview → registrar)

---

## 📞 Suporte

**Documentação Completa:** `docs/SMART_BILLING_SYSTEM.md`  
**Swagger UI:** http://localhost:8000/api/v1/docs  
**Backend Status:** http://localhost:8000/health (se disponível)

---

**Criado em:** 22/11/2025  
**Versão da API:** v1  
**Status:** ✅ Pronto para uso
