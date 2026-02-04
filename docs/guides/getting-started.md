# 🚀 Getting Started

Este guia vai ajudá-lo a configurar e executar o projeto Imobly localmente em menos de 10 minutos.

---

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Docker** (versão 20.10+) e **Docker Compose** (versão 2.0+)
- **Make** (Windows: `choco install make` ou use Git Bash)
- **Git**
- **Node.js 18+** (opcional, apenas se não usar Docker)
- **Python 3.11+** (opcional, apenas se não usar Docker)

### Verificar Instalação

```bash
docker --version
docker compose version
make --version
git --version
```

---

## 📁 Estrutura do Projeto

O Imobly é dividido em 3 repositórios independentes:

```
📦 Imobly/
├── 🔐 auth-api/          # Autenticação e usuários
├── ⚙️  Backend/          # Lógica de negócio (propriedades, contratos, etc)
└── 🎨 Frontend/          # Interface web (Next.js)
```

---

## 🛠️ Setup Inicial

### 1️⃣ Clonar Repositórios

```bash
# Crie um diretório para o projeto
mkdir imobly-project
cd imobly-project

# Clone os 3 repositórios
git clone https://github.com/Imobly/auth-api.git
git clone https://github.com/Imobly/Backend.git
git clone https://github.com/Imobly/Frontend.git
```

### 2️⃣ Configurar Variáveis de Ambiente

Em cada repositório, copie o arquivo de exemplo:

```bash
# Auth-api
cd auth-api
cp .env.example .env
cd ..

# Backend
cd Backend/Backend
cp .env.example .env
cd ../..

# Frontend
cd Frontend/Frontend
cp .env.example .env
cd ../..
```

!!! note "Variáveis Padrão"
    Os arquivos `.env.example` já vêm com configurações pré-definidas para desenvolvimento local. Você não precisa alterá-los inicialmente.

### 3️⃣ Criar Rede Docker

Os serviços precisam de uma rede compartilhada:

```bash
docker network create imovel_network
```

---

## 🚀 Executar o Projeto

### Opção 1: Usar Makefile (Recomendado)

Execute em cada repositório:

```bash
# Auth-api
cd auth-api
make run-dev

# Backend (novo terminal)
cd Backend/Backend
make run-dev

# Frontend (novo terminal)
cd Frontend/Frontend
make run-dev
```

### Opção 2: Docker Compose Direto

```bash
# Em cada repositório
docker compose up -d
```

### Opção 3: Script Automatizado

Se você tem um Makefile raiz configurado:

```bash
# Na raiz (onde estão os 3 repositórios)
make run-all-dev
```

---

## ✅ Verificar Instalação

### 1. Verificar Containers

```bash
docker ps

# Deve mostrar:
# - auth-api-auth-api-1 (porta 8001)
# - imobly_backend (porta 8000)
# - frontend-frontend-1 (porta 3000)
# - auth-api-postgres-1 (porta 5433)
# - imobly_postgres (porta 5432)
```

### 2. Testar Endpoints

```bash
# Auth API
curl http://localhost:8001/health
# Resposta: {"status":"healthy"}

# Backend
curl http://localhost:8000/health
# Resposta: {"status":"healthy","service":"Imóvel Gestão API (DEV)"}

# Frontend
curl http://localhost:3000
# Resposta: HTML da aplicação
```

### 3. Acessar Aplicação

Abra o navegador em: **http://localhost:3000**

---

## 👤 Criar Primeiro Usuário

### Via API (cURL)

```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "seu@email.com",
    "username": "seuusuario",
    "password": "SuaSenha123!",
    "full_name": "Seu Nome"
  }'
```

### Via Frontend

1. Acesse http://localhost:3000
2. Clique em "Criar conta"
3. Preencha os dados
4. Faça login

---

## 🔍 Explorando a Aplicação

### 📊 Dashboards

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/api/v1/docs
- **Auth API Docs**: http://localhost:8001/docs

### 📝 Dados de Teste

O banco de dados pode ser populado com dados de teste para desenvolvimento.

---

## 🛑 Parar os Serviços

```bash
# Com Makefile
cd <repositório>
make stop-dev

# Com Docker Compose
docker compose down

# Parar tudo e limpar volumes
make clean
```

---

## 🐛 Problemas Comuns

### Porta já em uso

Se as portas 3000, 8000, 8001, 5432 ou 5433 já estiverem em uso:

```bash
# Ver o que está usando a porta (Windows)
netstat -ano | findstr :8000

# Ver o que está usando a porta (Linux/Mac)
lsof -i :8000

# Parar o processo ou alterar a porta no docker-compose.yml
```

### Containers não iniciam

```bash
# Ver logs
docker compose logs -f

# Rebuildar imagens
make setup-dev
make run-dev
```

### Erro de conexão com banco

```bash
# Verificar se PostgreSQL está rodando
docker ps | grep postgres

# Recriar volumes
docker compose down -v
docker compose up -d
```

### Frontend não carrega dados

```bash
# Verificar variáveis de ambiente
cat Frontend/Frontend/.env

# Verificar se Backend está respondendo
curl http://localhost:8000/health

# Ver logs do Frontend
docker logs frontend-frontend-1
```

---

## 📚 Próximos Passos

Agora que o projeto está rodando:

1. 📖 **[Entenda a Arquitetura](architecture.md)** - Como os serviços se comunicam
2. 🔐 **[Configure Autenticação](../auth/index.md)** - Fluxo de login e tokens
3. 📊 **[Explore as APIs](../api/index.md)** - Endpoints disponíveis
4. 🚀 **[Deploy em Produção](deployment.md)** - Preparar para produção

---

## 🆘 Suporte

Encontrou algum problema?

- 📖 Verifique a [documentação completa](../index.md)
- 🐛 Abra uma issue no GitHub dos repositórios
- 💬 Entre em contato: devcostta@gmail.com

---

**✅ Pronto! O projeto está rodando localmente.**
