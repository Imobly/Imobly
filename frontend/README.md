# Imobly - Sistema de Gestão Imobiliária

Sistema moderno de gestão imobiliária desenvolvido com Next.js 14, TypeScript e TailwindCSS. Gerencie propriedades, inquilinos, pagamentos e despesas de forma integrada e eficiente.

## 🌐 Aplicação em Produção

- **Frontend**: https://imobly.onrender.com
- **Backend API**: https://backend-non0.onrender.com
- **Documentação**: https://imobly.github.io/Documentation/

> Não há um serviço de Auth API separado. A autenticação é feita pelo
> Supabase Auth; o backend único (FastAPI) valida o JWT do Supabase.

## 🚀 Tecnologias

- **Framework**: Next.js 14 (App Router)
- **Linguagem**: TypeScript 5
- **Estilização**: TailwindCSS, Radix UI, shadcn/ui
- **Ícones**: Lucide React
- **HTTP Client**: Axios
- **Formulários**: React Hook Form + Zod
- **Gráficos**: Recharts

## 🔧 Rodar Localmente

### Pré-requisitos

- Node.js 20+ (o projeto fixa `pnpm@9.15.9` via `packageManager` em
  `package.json` — use `corepack enable` para que essa versão seja
  resolvida automaticamente)
- Backend rodando em `localhost:8000` (FastAPI) — veja
  [`../backend/README.md`](../backend/README.md)

### Instalação

```bash
git clone https://github.com/Imobly/Frontend.git
cd Frontend
```

### 2. Instale as dependências

```bash
pnpm install
```

### 3. Configure as variáveis de ambiente

Copie o arquivo de exemplo e configure:

```bash
cp .env.example .env.local
```

O arquivo `.env.local` deve conter (apenas variáveis públicas, sem segredos). Use APIs locais por padrão; se preferir dados reais, substitua por URLs de produção:

```env
# API local (recomendado em DEV)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Supabase público (necessário — auth e storage passam por aqui)
NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=public-anon-key

NEXT_PUBLIC_APP_NAME=Imobly
NEXT_PUBLIC_APP_VERSION=1.0.0
NODE_ENV=development

# Alternativa: usar a API de produção para desenvolvimento com dados reais
# NEXT_PUBLIC_API_URL=https://backend-non0.onrender.com/api/v1
```

### 4. Inicie o backend

**Importante**: o frontend depende do backend para funcionar. Não há um
serviço de Auth API separado — a autenticação passa pelo Supabase, validado
pelo próprio backend.

```bash
# Em um terminal separado, inicie o Backend (porta 8000)
cd ../backend
# Siga as instruções do README do backend
```

### 5. Execute o servidor de desenvolvimento

```bash
pnpm dev
```

O frontend estará disponível em: **http://localhost:3000**

## 📋 Scripts Disponíveis

```bash
pnpm dev          # Servidor de desenvolvimento (porta 3000)
pnpm build        # Build de produção
pnpm start        # Servidor de produção (após build)
pnpm lint         # Executar ESLint
```
## 🏗️ Estrutura do Projeto

```
Frontend/
├── app/                    # App Router (Next.js 14)
│   ├── login/             # Autenticação
│   ├── dashboard/         # Dashboard principal
│   ├── properties/        # Gestão de propriedades
│   ├── tenants/           # Gestão de inquilinos
│   ├── payments/          # Gestão de pagamentos
│   └── expenses/          # Gestão de despesas
├── components/            # Componentes React
│   ├── ui/               # Componentes UI (shadcn/ui)
│   └── [feature]/        # Componentes por funcionalidade
├── lib/
│   ├── api/              # Serviços da API
│   └── types/            # TypeScript types
└── public/               # Arquivos estáticos
```

## 🌐 Deploy e Ambientes

- Ambientes (DEV, HML, PROD): https://imobly.github.io/Documentation/guides/environments/
- Deploy: https://github.com/Imobly/docs

## 🐛 Troubleshooting

- Erro "Failed to fetch" no login: garanta que o Backend está de pé em
  `localhost:8000` e confirme `NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_SUPABASE_URL`
  em `.env.local`.
- Porta 3000 em uso (Windows): `netstat -ano | findstr :3000` e finalize o processo se necessário.
- `pnpm install` falhando com "This version of pnpm requires at least Node.js
  vXX" — sua versão de Node é anterior à exigida pela versão de `pnpm`
  instalada. Rode `corepack enable` na raiz do projeto: o Corepack lê o campo
  `packageManager` de `package.json` e resolve a versão de pnpm correta (fixada
  em `9.15.9`) automaticamente, sem depender de `pnpm@latest`.
- Ao rodar via Docker: se um build **sem cache** (`docker compose build
  --no-cache`) falhar num passo de instalação que sempre funcionou antes, é
  quase sempre uma tag flutuante (`@latest`) resolvendo para uma versão nova
  incompatível — não uma mudança no código do projeto. Prefira `docker compose
  build --no-cache` periodicamente para pegar esse tipo de quebra antes que
  ela apareça só em CI ou num ambiente novo.

### Docker no Windows: `ENOMEM` e compilação lenta

Rodando via Docker Desktop no Windows, os logs do frontend mostram
`Error: ENOMEM: not enough memory, scandir '/app/app'` e o primeiro acesso a
cada rota leva 30–60s.

**Isso não é falta de memória** — o container não tem limite definido e usa
~1 GB de 7,4 GB disponíveis; o diretório em questão tem poucas dezenas de
arquivos. É uma limitação conhecida da camada de compartilhamento de arquivos
do Docker Desktop no Windows (WSL2/FUSE), que devolve `ENOMEM` em `readdir`
sobre bind mount. O Next.js registra o erro e segue: **as páginas compilam e
respondem 200 normalmente**, apenas devagar no primeiro acesso.

Se a lentidão incomodar, em ordem de eficácia:

1. Mover o repositório para dentro do sistema de arquivos do WSL2
   (`\\wsl$\Ubuntu\home\<user>\...`) e rodar o Docker de lá — elimina a
   travessia Windows↔Linux e é de longe o maior ganho.
2. Rodar o frontend direto no host (`pnpm dev`), deixando só o backend no
   Docker.
3. Conviver: depois do primeiro compile, cada rota responde rápido.

O `docker-compose.yml` já define `WATCHPACK_POLLING`/`CHOKIDAR_USEPOLLING`,
necessários porque bind mounts do Windows não propagam eventos inotify — sem
isso o hot reload não dispara.
## 📄 Licença

Este projeto é propriedade da **Imobly**.

---
**Desenvolvido pela equipe Imobly** • [Organização GitHub](https://github.com/Imobly)
Para documentação completa, acesse: https://imobly.github.io/Documentation/
