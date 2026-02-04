# 🚀 Guia de Deployment

Este guia fornece instruções completas para fazer o deploy do Imobly em produção usando Docker e Supabase.

---

## 📋 Pré-requisitos

Antes de começar o deploy, certifique-se de ter:

- **Servidor Linux** (Ubuntu 20.04+ recomendado) ou Windows Server
- **Docker** (20.10+) e **Docker Compose** (2.0+) instalados
- **Conta Supabase** criada (https://supabase.com)
- **Domínio configurado** (opcional, mas recomendado)
- **Certificado SSL** (Let's Encrypt ou similar)

---

## 🗄️ 1. Configurar Supabase

### 1.1 Criar Projeto no Supabase

1. Acesse https://supabase.com e faça login
2. Clique em "New Project"
3. Preencha:
   - **Name:** Imobly Auth
   - **Database Password:** Gere uma senha forte
   - **Region:** Escolha mais próximo aos usuários

### 1.2 Obter Credenciais

No painel do projeto:

1. Vá em **Settings** → **Database**
2. Role até **Connection String**
3. Copie a **Transaction Mode Connection String** (porta 6543)

Exemplo:
```
postgresql://postgres.xxxxx:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true
```

### 1.3 Criar Segundo Banco (opcional)

Para separar `auth_db` e `imovel_gestao`:

**Opção A:** Usar schemas no mesmo banco
```sql
CREATE SCHEMA auth;
CREATE SCHEMA business;
```

**Opção B:** Criar segundo projeto Supabase
- Repita os passos 1.1 e 1.2 para ter dois bancos independentes

---

## 🔐 2. Gerar SECRET_KEY

A SECRET_KEY deve ser a **mesma** no Auth API e Backend:

```bash
# Gerar SECRET_KEY de 32 bytes
openssl rand -hex 32

# Exemplo de saída:
# a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

!!! danger "Importante"
    - Guarde essa SECRET_KEY em um local seguro
    - Use a MESMA chave no Auth API e Backend
    - NUNCA commite a SECRET_KEY no Git

---

## 📝 3. Configurar Variáveis de Ambiente

### 3.1 Auth API

Crie o arquivo `.env.prod` no repositório Auth-api:

```bash
# Auth-api/.env.prod
DATABASE_URL=postgresql://postgres.xxxxx:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true
SECRET_KEY=<sua-secret-key-de-32-bytes>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3.2 Backend

Crie o arquivo `.env.prod` no repositório Backend:

```bash
# Backend/Backend/.env.prod
DATABASE_URL=postgresql://postgres.xxxxx:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true
AUTH_API_SECRET_KEY=<MESMA-SECRET-KEY-DO-AUTH-API>
ALGORITHM=HS256
AUTH_API_URL=https://auth.seudominio.com
```

### 3.3 Frontend

Crie o arquivo `.env.prod` no repositório Frontend:

```bash
# Frontend/Frontend/.env.prod
NEXT_PUBLIC_API_URL=https://api.seudominio.com
NEXT_PUBLIC_AUTH_API_URL=https://auth.seudominio.com
```

---

## 🐳 4. Deploy com Docker

### 4.1 Fazer Build das Imagens

Em cada repositório:

```bash
# Auth-api
cd auth-api
make setup-prod
make deploy

# Backend
cd ../Backend/Backend
make setup-prod
make deploy

# Frontend
cd ../Frontend/Frontend
make setup-prod
make deploy
```

### 4.2 Verificar Containers

```bash
docker ps

# Deve mostrar:
# - auth-api-auth-api-1
# - imobly_backend
# - frontend-frontend-1
```

### 4.3 Verificar Health

```bash
# Auth API
curl https://auth.seudominio.com/health

# Backend
curl https://api.seudominio.com/health

# Frontend
curl https://seudominio.com
```

---

## 🌐 5. Configurar Nginx (Reverse Proxy)

### 5.1 Instalar Nginx

```bash
sudo apt update
sudo apt install nginx -y
```

### 5.2 Configurar Reverse Proxy

Crie `/etc/nginx/sites-available/imobly`:

```nginx
# Frontend
server {
    listen 80;
    server_name seudominio.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# Backend API
server {
    listen 80;
    server_name api.seudominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# Auth API
server {
    listen 80;
    server_name auth.seudominio.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 5.3 Habilitar Site

```bash
sudo ln -s /etc/nginx/sites-available/imobly /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔒 6. Configurar SSL (HTTPS)

### 6.1 Instalar Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 6.2 Obter Certificado

```bash
sudo certbot --nginx -d seudominio.com -d api.seudominio.com -d auth.seudominio.com
```

### 6.3 Renovação Automática

```bash
# Testar renovação
sudo certbot renew --dry-run

# Certbot adiciona cron automaticamente
```

---

## 🗃️ 7. Migrações de Banco de Dados

### 7.1 Auth API

```bash
cd auth-api
docker compose -f docker-compose.prod.yml exec auth-api alembic upgrade head
```

### 7.2 Backend

```bash
cd Backend/Backend
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

---

## 📊 8. Monitoramento

### 8.1 Ver Logs

```bash
# Auth API
docker logs -f auth-api-auth-api-1

# Backend
docker logs -f imobly_backend

# Frontend
docker logs -f frontend-frontend-1
```

### 8.2 Healthcheck

Crie um script `healthcheck.sh`:

```bash
#!/bin/bash

echo "Verificando serviços..."

# Auth API
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Auth API: OK"
else
    echo "❌ Auth API: FALHOU"
fi

# Backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend: OK"
else
    echo "❌ Backend: FALHOU"
fi

# Frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend: OK"
else
    echo "❌ Frontend: FALHOU"
fi
```

### 8.3 Configurar Cronjob

```bash
# Executar healthcheck a cada 5 minutos
crontab -e

# Adicionar linha:
*/5 * * * * /path/to/healthcheck.sh >> /var/log/imobly-health.log 2>&1
```

---

## 🔄 9. Atualizações

### 9.1 Pull da Nova Versão

```bash
cd auth-api
git pull origin main

cd ../Backend/Backend
git pull origin main

cd ../Frontend/Frontend
git pull origin develop
```

### 9.2 Rebuild e Deploy

```bash
# Em cada repositório
make deploy
```

---

## 🐛 10. Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker logs <container-id>

# Rebuild imagem
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

### Erro de conexão com Supabase

```bash
# Verificar DATABASE_URL
docker compose -f docker-compose.prod.yml exec backend env | grep DATABASE_URL

# Testar conexão manual
docker compose -f docker-compose.prod.yml exec backend python -c "from sqlalchemy import create_engine; engine = create_engine('postgresql://...'); print(engine.connect())"
```

### Token inválido entre serviços

```bash
# Verificar SECRET_KEY são iguais
docker compose -f docker-compose.prod.yml exec auth-api env | grep SECRET_KEY
docker compose -f docker-compose.prod.yml exec backend env | grep AUTH_API_SECRET_KEY

# Devem ser EXATAMENTE iguais
```

### Frontend não conecta ao Backend

```bash
# Verificar variáveis de ambiente
docker compose -f docker-compose.prod.yml exec frontend env | grep NEXT_PUBLIC

# Rebuild frontend com variáveis corretas
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

---

## 📋 11. Checklist de Deploy

- [ ] Supabase configurado e credenciais copiadas
- [ ] SECRET_KEY gerada e sincronizada entre Auth API e Backend
- [ ] Arquivos `.env.prod` criados em todos os repositórios
- [ ] Docker e Docker Compose instalados no servidor
- [ ] Imagens buildadas com sucesso
- [ ] Containers rodando (`docker ps`)
- [ ] Healthcheck passando em todos os serviços
- [ ] Nginx configurado como reverse proxy
- [ ] SSL/HTTPS configurado com Certbot
- [ ] DNS apontando para o servidor
- [ ] Migrações de banco executadas
- [ ] Logs configurados e monitoramento ativo
- [ ] Backup automático configurado (se necessário)

---

## 🔗 12. Recursos Adicionais

- [Supabase Documentation](https://supabase.com/docs)
- [Docker Documentation](https://docs.docker.com)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

---

## 📞 Suporte

Encontrou problemas no deploy?

- 📖 Verifique a [documentação completa](../index.md)
- 🏗️ Revise a [arquitetura do sistema](architecture.md)
- 🐛 Abra uma issue no GitHub

---

**🚀 Deploy completo! Seu Imobly está em produção.**
