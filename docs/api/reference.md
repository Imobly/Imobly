# Referência Completa da API

Esta página contém a documentação técnica completa de todos os endpoints da API Imobly.

!!! info "Documentação Interativa"
    Para testar os endpoints interativamente, utilize a documentação Swagger:
    
    - **Backend API:** [backend-non0.onrender.com/docs](https://backend-non0.onrender.com/docs)
    - **Auth API:** [auth-api-3zxk.onrender.com/docs](https://auth-api-3zxk.onrender.com/docs)

## Base URLs

### Produção
```
Backend: https://backend-non0.onrender.com/api/v1
Auth:    https://auth-api-3zxk.onrender.com/api/v1/auth
```

### Desenvolvimento Local
```
Backend: http://localhost:8000/api/v1
Auth:    http://localhost:8001/api/v1/auth
```

## Autenticação

Todos os endpoints requerem Bearer Token:

```http
Authorization: Bearer {seu_token_jwt}
```

### Obter Token

```http
POST /api/v1/auth/login
Content-Type: application/json

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

---

## Endpoints Detalhados

Para a documentação completa de todos os endpoints, incluindo:

- Parâmetros detalhados
- Exemplos de requisição/resposta
- Validações e regras de negócio
- Códigos de erro
- Exemplos de uso em TypeScript/React

Consulte o arquivo completo: **[API_REFERENCE_FRONTEND.md](https://github.com/Imobly/Documentation/blob/main/API_REFERENCE_FRONTEND.md)**

### Resumo dos Recursos

| Recurso | Endpoint Base | Descrição |
|---------|---------------|-----------|
| **Properties** | `/properties` | Gerenciamento de imóveis |
| **Tenants** | `/tenants` | Gerenciamento de inquilinos |
| **Contracts** | `/contracts` | Contratos de locação |
| **Payments** | `/payments` | Sistema de pagamentos |
| **Expenses** | `/expenses/` | Gestão de despesas (⚠️ trailing slash) |
| **Dashboard** | `/dashboard` | Estatísticas e métricas |
| **Notifications** | `/notifications` | Sistema de notificações |

---

## Notas Importantes

### 🔒 Multi-Tenancy

Todos os endpoints implementam isolamento por usuário. Cada usuário vê apenas seus próprios dados.

### 🌐 Trailing Slashes

!!! danger "Atenção"
    Endpoints autenticados de **Expenses** requerem `/` no final da URL para evitar perda do token de autenticação!
    
    - ✅ `/api/v1/expenses/`
    - ❌ `/api/v1/expenses`

### 📊 Paginação

Endpoints de listagem suportam paginação via query parameters:

- `skip` (int): Registros a pular (default: 0)
- `limit` (int): Máximo de registros (default: 100)

### 🔄 Códigos HTTP

| Código | Significado |
|--------|-------------|
| 200 | OK |
| 201 | Criado |
| 204 | Sem conteúdo (deletado) |
| 400 | Requisição inválida |
| 401 | Não autenticado |
| 403 | Sem permissão (multi-tenancy) |
| 404 | Não encontrado |
| 422 | Validação falhou |
| 500 | Erro interno do servidor |

---

## Guias de Integração

### Setup Inicial (TypeScript)

```typescript
// api-client.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://backend-non0.onrender.com/api/v1',
  timeout: 30000
});

// Interceptor para adicionar token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para tratar erros
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token inválido - redirecionar para login
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Fluxo de Autenticação

```typescript
// auth.service.ts
import api from './api-client';

export const authService = {
  async login(username: string, password: string) {
    const { data } = await axios.post(
      'https://auth-api-3zxk.onrender.com/api/v1/auth/login',
      { username, password }
    );
    
    localStorage.setItem('access_token', data.access_token);
    return data;
  },

  async register(email: string, password: string, name: string) {
    const { data } = await axios.post(
      'https://auth-api-3zxk.onrender.com/api/v1/auth/register',
      { email, password, name }
    );
    return data;
  },

  async getMe() {
    const { data } = await axios.get(
      'https://auth-api-3zxk.onrender.com/api/v1/auth/me',
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      }
    );
    return data;
  },

  logout() {
    localStorage.removeItem('access_token');
  }
};
```

### Exemplo Completo - CRUD de Propriedades

```typescript
// properties.service.ts
import api from './api-client';

interface Property {
  id?: number;
  name: string;
  address: string;
  neighborhood: string;
  city: string;
  state: string;
  zip_code: string;
  type: 'apartment' | 'house' | 'commercial' | 'studio';
  area: number;
  bedrooms: number;
  bathrooms: number;
  parking_spaces: number;
  rent: number;
  status: 'vacant' | 'occupied' | 'maintenance' | 'inactive';
  description?: string;
  is_residential: boolean;
}

export const propertyService = {
  async list(params?: {
    skip?: number;
    limit?: number;
    property_type?: string;
    status?: string;
  }) {
    const { data } = await api.get<Property[]>('/properties', { params });
    return data;
  },

  async getById(id: number) {
    const { data } = await api.get<Property>(`/properties/${id}`);
    return data;
  },

  async create(property: Omit<Property, 'id'>) {
    const { data } = await api.post<Property>('/properties', property);
    return data;
  },

  async update(id: number, updates: Partial<Property>) {
    const { data } = await api.put<Property>(`/properties/${id}`, updates);
    return data;
  },

  async delete(id: number) {
    await api.delete(`/properties/${id}`);
  },

  async uploadImages(id: number, files: File[]) {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    const { data } = await api.post(
      `/properties/${id}/upload-images`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    );
    return data;
  }
};
```

---

## Testes e Validação

### Testando a Conexão

```bash
# Verificar status da API
curl https://backend-non0.onrender.com/api/v1/

# Fazer login e obter token
curl -X POST https://auth-api-3zxk.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@test.com","password":"test123"}'

# Listar propriedades (substitua TOKEN)
curl https://backend-non0.onrender.com/api/v1/properties \
  -H "Authorization: Bearer TOKEN"
```

### Ferramentas Recomendadas

- **Postman/Insomnia:** Para testes manuais de API
- **Swagger UI:** Documentação interativa integrada
- **cURL:** Testes rápidos via linha de comando

---

## Suporte

Encontrou algum problema ou tem dúvidas?

- 📚 **Documentação Completa:** [API_REFERENCE_FRONTEND.md](https://github.com/Imobly/Documentation/blob/main/API_REFERENCE_FRONTEND.md)
- 🐛 **Reportar Bug:** [GitHub Issues](https://github.com/Imobly/Documentation/issues)
- 📧 **Email:** devcostta@gmail.com
- 💬 **Discussões:** [GitHub Discussions](https://github.com/Imobly/Documentation/discussions)
