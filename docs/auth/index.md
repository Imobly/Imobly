# Autenticação

O sistema de autenticação do Imobly é baseado em **JWT (JSON Web Tokens)** para controle de acesso às APIs.

## Visão Geral

O sistema implementa:

- **Autenticação JWT** com tokens de acesso
- **Validação de credenciais** com hash bcrypt
- **Proteção de endpoints** da API
- **Sistema básico de usuários**

## Endpoints de Autenticação

### Registro de Usuário

**POST** `/api/v1/auth/register`

Cria uma nova conta de usuário.

**Request Body:**

```json
{
  "name": "João Silva",
  "email": "joao@exemplo.com",
  "password": "senha_segura_123"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "name": "João Silva",
      "email": "joao@exemplo.com",
      "is_active": true,
      "created_at": "2024-01-01T10:00:00Z"
    }
  },
  "message": "Usuário criado com sucesso"
}
```

### Login

**POST** `/api/v1/auth/login`

Autentica um usuário e retorna um token JWT.

**Request Body:**

```json
{
  "email": "joao@exemplo.com",
  "password": "senha_segura_123"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": 1,
      "name": "João Silva",
      "email": "joao@exemplo.com"
    }
  },
  "message": "Login realizado com sucesso"
}
```

### Logout

**POST** `/api/v1/auth/logout`

Invalida o token do usuário.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response:**

```json
{
  "success": true,
  "message": "Logout realizado com sucesso"
}
```

## Configuração JWT

### Variáveis de Ambiente

```env
SECRET_KEY=sua-chave-super-secreta-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Estrutura do Token

```json
{
  "sub": "1",
  "email": "joao@exemplo.com",
  "name": "João Silva",
  "exp": 1699123456,
  "iat": 1699119856
}
```

## Utilizando a Autenticação

### Em Requisições HTTP

Inclua o token no header `Authorization`:

```bash
curl -X GET "http://localhost:8000/api/v1/properties" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Validação de Senha

O sistema valida:

- **Comprimento mínimo:** 8 caracteres
- **Complexidade básica:** recomendado letras e números

### Hash de Senhas

- **Algoritmo:** bcrypt
- **Rounds:** 12 (padrão)
- **Salt:** gerado automaticamente

## Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 401 | Token inválido ou expirado |
| 422 | Dados de entrada inválidos |
| 404 | Usuário não encontrado |
| 400 | Credenciais incorretas |

## Exemplo de Uso

### 1. Registrar usuário

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva",
    "email": "joao@exemplo.com", 
    "password": "minhasenha123"
  }'
```

### 2. Fazer login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "joao@exemplo.com",
    "password": "minhasenha123"
  }'
```

### 3. Usar token em requisições

```bash
curl -X GET "http://localhost:8000/api/v1/properties" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## Segurança

### Boas Práticas

- Mantenha o `SECRET_KEY` seguro e único
- Use HTTPS em produção
- Configure tempo de expiração adequado para tokens
- Não armazene tokens em localStorage (use httpOnly cookies quando possível)

### Rate Limiting

O sistema pode implementar limitação de tentativas:

- Login: 5 tentativas por minuto por IP
- Registro: 3 tentativas por hora por IP

## Troubleshooting

### Token Expirado

**Erro:** `401 Unauthorized - Token expired`

**Solução:** Faça login novamente para obter um novo token.

### Credenciais Inválidas

**Erro:** `400 Bad Request - Invalid credentials`

**Solução:** Verifique email e senha estão corretos.

### Token Malformado

**Erro:** `401 Unauthorized - Invalid token format`

**Solução:** Verifique se o token está sendo enviado corretamente no header Authorization.