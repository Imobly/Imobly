# Ambientes (DEV, HML, PROD)

Este guia explica como funcionam os ambientes de desenvolvimento (DEV), homologação (HML) e produção (PROD) no projeto Imobly, como alternar entre eles e quais arquivos alterar em cada serviço (Auth API, Backend e Frontend).

## Visão geral
- **DEV**: Executa localmente com Docker; por padrão consome o banco de **HML** para evitar dados reais e simplificar testes.
- **HML**: Ambiente de homologação; usa banco separado no Supabase (recomendado) ou Postgres dedicado.
- **PROD**: Produção; usa banco de produção no Supabase. Deve ser claramente separado de HML.

Todos os serviços usam um **único arquivo `.env` por repositório** com a variável seletora `ENVIRONMENT` e três DSNs configuráveis: `DATABASE_URL_DEV`, `DATABASE_URL_HML`, `DATABASE_URL_PROD`. O código resolve automaticamente qual DSN usar com base em `ENVIRONMENT` (com overrides do `docker-compose` quando aplicável).

## Onde configurar
- Auth API: [Auth-api/.env](Auth-api/.env) e os `docker-compose` [Auth-api/docker-compose.yml](Auth-api/docker-compose.yml), [Auth-api/docker-compose.prod.yml](Auth-api/docker-compose.prod.yml)
- Backend: [Backend/Backend/.env](Backend/Backend/.env) e os `docker-compose` [Backend/Backend/docker-compose.yml](Backend/Backend/docker-compose.yml), [Backend/Backend/docker-compose.prod.yml](Backend/Backend/docker-compose.prod.yml)
- Frontend: [Frontend/Frontend/.env](Frontend/Frontend/.env) e [Frontend/Frontend/docker-compose.yml](Frontend/Frontend/docker-compose.yml)

Para referência geral de comandos, veja o Makefile raiz: [Makefile](Makefile)

## Variáveis de ambiente chave
- `ENVIRONMENT`: `development` | `staging` | `production`
  - `development` → usa `DATABASE_URL_DEV`
  - `staging` → usa `DATABASE_URL_HML`
  - `production` → usa `DATABASE_URL_PROD`
- `DATABASE_URL_DEV` / `HML` / `PROD`: DSNs completos do Postgres.
  - Em Supabase com PgBouncer (Transaction Pooler), use porta `6543` e `sslmode=require`, por exemplo:
    - `postgresql://<user>:<pass>@<host>:6543/<db>?sslmode=require`
- `DB_SCHEMA`: Nome do schema por serviço. Exemplo: `auth_api` para Auth API.
- `BACKEND_CORS_ORIGINS` e `CORS_ORIGINS`: Lista de origens permitidas, separadas por vírgula. Ex.: `http://localhost:3000,https://demo.imobly.com`
- Frontend (público, sem segredos): `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_AUTH_API_URL`, opcionalmente `NEXT_PUBLIC_SUPABASE_URL` e `NEXT_PUBLIC_SUPABASE_ANON_KEY`.

## Como alternar entre DEV, HML e PROD

### Desenvolvimento (usa HML por padrão)
1. Ajuste `ENVIRONMENT=staging` nos `.env` de Auth API e Backend:
   - [Auth-api/.env](Auth-api/.env)
   - [Backend/Backend/.env](Backend/Backend/.env)
2. Defina `DATABASE_URL_HML` com o DSN do banco HML (Supabase recomendado).
3. No Frontend, confirme URLs públicas usando localhost:
   - [Frontend/Frontend/.env](Frontend/Frontend/.env):
     - `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
     - `NEXT_PUBLIC_AUTH_API_URL=http://localhost:8001/api/v1/auth`
4. Suba todos os serviços de DEV:
   - `make run-all-dev`

Dica: os `docker-compose` de DEV já sobrepõem `ENVIRONMENT=staging` e apontam para `DATABASE_URL_HML` conforme configurado.

### Homologação (HML)
- Em uma infraestrutura HML, use `.env` com `ENVIRONMENT=staging` e `DATABASE_URL_HML` adequado.
- Se precisar rodar local apontando para HML (default), basta `make run-all-dev` como acima.

### Produção (PROD)
1. Ajuste `ENVIRONMENT=production` nos `.env` de Auth API e Backend.
2. Defina `DATABASE_URL_PROD` com o DSN de produção (Supabase com porta 6543, `sslmode=require`).
3. Suba os serviços de produção:
   - `make run-all`

Os `docker-compose.prod.yml` de cada serviço reforçam `ENVIRONMENT=production` e usam `DATABASE_URL_PROD`.

## Configuração por serviço

### Auth API
- `.env` unificado: [Auth-api/.env](Auth-api/.env)
- Resolve DB por `ENVIRONMENT` dentro de [Auth-api/app/core/config.py](Auth-api/app/core/config.py).
- `DB_SCHEMA` padrão sugerido: `auth_api`.
- CORS: `CORS_ORIGINS` separadas por vírgula.
- Compose:
  - DEV: [Auth-api/docker-compose.yml](Auth-api/docker-compose.yml) → `ENVIRONMENT=staging`, `DATABASE_URL=${DATABASE_URL_HML}`
  - PROD: [Auth-api/docker-compose.prod.yml](Auth-api/docker-compose.prod.yml) → `ENVIRONMENT=production`, `DATABASE_URL=${DATABASE_URL_PROD}`

### Backend
- `.env` unificado: [Backend/Backend/.env](Backend/Backend/.env)
- Resolve DB e CORS em [Backend/Backend/app/core/config.py](Backend/Backend/app/core/config.py); o app usa `settings.cors_origins_list` já parseado.
- Compose:
  - DEV: [Backend/Backend/docker-compose.yml](Backend/Backend/docker-compose.yml) → `ENVIRONMENT=staging`, `DATABASE_URL=${DATABASE_URL_HML}`
  - PROD: [Backend/Backend/docker-compose.prod.yml](Backend/Backend/docker-compose.prod.yml) → `ENVIRONMENT=production`, `DATABASE_URL=${DATABASE_URL_PROD}`

### Frontend
- `.env` público: [Frontend/Frontend/.env](Frontend/Frontend/.env)
- Mapeamento de variáveis em [Frontend/Frontend/next.config.mjs](Frontend/Frontend/next.config.mjs)
- Compose DEV: [Frontend/Frontend/docker-compose.yml](Frontend/Frontend/docker-compose.yml)
- Não colocar DSNs de banco no Frontend. Apenas chaves públicas como `NEXT_PUBLIC_SUPABASE_ANON_KEY`.

## Comandos úteis
- `make setup-all-dev` / `make run-all-dev` / `make stop-all-dev` / `make restart-all-dev`
- `make setup-all` / `make run-all` / `make stop-all`
- `make health-all` para checar saúde dos serviços
- Por serviço: `cd Auth-api && make help`, `cd Backend/Backend && make help`, `cd Frontend/Frontend && make help`

## Boas práticas
- Separe bancos HML e PROD com credenciais e hosts distintos.
- Use PgBouncer (porta 6543) com `sslmode=require` em Supabase.
- Mantenha um `.env` por repositório e `.env.example` claro com os três DSNs.
- Em DEV, preferir consumir HML para evitar dados reais.

## Troubleshooting
- net::ERR_NAME_NOT_RESOLVED no Frontend: não use hostnames de containers (ex.: `imobly_backend`) no browser. Use `http://localhost:8000/...` e `http://localhost:8001/...`.
- CORS bloqueando requisições: ajuste `BACKEND_CORS_ORIGINS` e `CORS_ORIGINS` com as origens corretas (separadas por vírgula). O Backend já faz o parsing interno.
- DEV apontando para PROD: verifique se `DATABASE_URL_HML` e `DATABASE_URL_PROD` não são idênticos; defina DSNs distintos.
