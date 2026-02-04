# 🚀 Guia Rápido - Imobly Monorepo

## 📍 Localização do Projeto

```
C:\Users\jvand\Documents\Imobly-Monorepo\
```

---

## ⚡ Comandos Mais Usados

### Iniciar Projeto (Docker)
```bash
cd C:\Users\jvand\Documents\Imobly-Monorepo
docker-compose up
```

### Parar Projeto
```bash
# Ctrl+C no terminal
# OU
docker-compose down
```

### Ver Logs
```bash
docker-compose logs -f
```

### Reiniciar Serviços
```bash
docker-compose restart
```

---

## 🔧 Desenvolvimento Local (Sem Docker)

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
pnpm install
pnpm dev
```

---

## 📦 Instalação de Dependências

### Backend
```bash
cd backend
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
pnpm install
```

### Supabase (Frontend)
```bash
cd frontend
pnpm add @supabase/supabase-js @supabase/auth-helpers-nextjs
```

---

## 🧪 Testes

### Backend
```bash
cd backend
pytest -v
```

### Frontend
```bash
cd frontend
pnpm test
```

---

## 🎨 Lint e Format

### Backend
```bash
cd backend
flake8 app
black app
isort app
```

### Frontend
```bash
cd frontend
pnpm lint
pnpm format
```

---

## 🗄️ Banco de Dados

### Criar Tabelas
```bash
cd backend
python -c "from app.db.session import create_tables; create_tables()"
```

### Migrations (Alembic)
```bash
cd backend
alembic revision --autogenerate -m "descrição"
alembic upgrade head
```

---

## 🔐 Configurar Supabase

### 1. Criar Projeto
- Acesse: https://supabase.com/dashboard
- "New Project" → Nome: `Imobly`

### 2. Obter Credenciais
- Settings → API
- Copiar: URL, anon key, service_role key

### 3. Atualizar .env

**Backend**:
```bash
cd backend
cp .env.example .env
code .env
```

**Frontend**:
```bash
cd frontend
cp .env.local.example .env.local
code .env.local
```

---

## 🌐 URLs Importantes

- **Backend API**: http://localhost:8000
- **Backend Docs**: http://localhost:8000/api/v1/docs
- **Frontend**: http://localhost:3000
- **Supabase Dashboard**: https://supabase.com/dashboard

---

## 📂 Arquivos Importantes

- **Backend .env**: `backend/.env`
- **Frontend .env**: `frontend/.env.local`
- **Docker Compose**: `docker-compose.yml`
- **Makefile**: `Makefile`
- **Docs**: `docs/`
- **Supabase Auth**: `docs/auth/supabase-setup.md`

---

## 🔄 Git

### Status
```bash
git status
```

### Commit
```bash
git add .
git commit -m "feat: descrição"
```

### Push
```bash
git push origin main
```

### Criar Remote (Primeira Vez)
```bash
git remote add origin https://github.com/Imobly/Imobly.git
git branch -M main
git push -u origin main
```

---

## 📋 Checklist Diário

### Ao Iniciar
- [ ] Abrir terminal no diretório do projeto
- [ ] Verificar se Docker está rodando
- [ ] `docker-compose up`
- [ ] Acessar http://localhost:3000

### Ao Desenvolver
- [ ] Criar branch para feature: `git checkout -b feature/nome`
- [ ] Fazer commits frequentes
- [ ] Rodar testes antes de commitar

### Ao Finalizar
- [ ] `docker-compose down`
- [ ] Commit final
- [ ] Push para GitHub

---

## 🆘 Troubleshooting

### Backend não inicia
```bash
# Ver logs
docker-compose logs backend

# Verificar .env
code backend/.env

# Recriar container
docker-compose down
docker-compose up --build backend
```

### Frontend não inicia
```bash
# Ver logs
docker-compose logs frontend

# Limpar node_modules
cd frontend
Remove-Item -Recurse -Force node_modules
pnpm install

# Rebuild
docker-compose up --build frontend
```

### Erro de conexão com DB
```bash
# Verificar se DB está rodando
docker-compose ps

# Reiniciar DB
docker-compose restart db
```

### Erro "Invalid token"
```typescript
// Frontend: Verificar se token está sendo enviado
const { data: { session } } = await supabase.auth.getSession()
console.log('Token:', session?.access_token)

// Backend: Ver logs
docker-compose logs backend | grep -i "token"
```

---

## 🎯 Fluxo de Trabalho Típico

```bash
# 1. Atualizar código
git pull origin main

# 2. Iniciar projeto
docker-compose up -d

# 3. Desenvolver
# Editar código, testar, etc

# 4. Commit
git add .
git commit -m "feat: nova funcionalidade"

# 5. Push
git push origin main

# 6. Parar projeto
docker-compose down
```

---

## 📞 Contato e Suporte

- **Documentação**: `docs/`
- **Backup**: `C:\Backup-Imobly-20260204-120604\`
- **Issues**: GitHub Issues (quando criar repo)

---

**💡 Dica**: Mantenha este arquivo aberto para referência rápida!
