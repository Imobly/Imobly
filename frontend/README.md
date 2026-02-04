# Imobly - Sistema de Gestão Imobiliária

Sistema moderno de gestão imobiliária desenvolvido com Next.js 14, TypeScript e TailwindCSS. Gerencie propriedades, inquilinos, pagamentos e despesas de forma integrada e eficiente.

## 🌐 Aplicação em Produção

- **Frontend**: https://imobly.onrender.com
- **Backend API**: https://backend-non0.onrender.com
- **Auth API**: https://auth-api-3zxk.onrender.com
- **Documentação**: https://imobly.github.io/Documentation/

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

- Node.js 18+
- pnpm (recomendado) ou npm

### Instalação
Para rodar este projeto localmente, você precisa:

- Node.js 18+
- pnpm (recomendado) ou npm
- Backend rodando em `localhost:8000` (FastAPI)
- Auth API rodando em `localhost:8001`

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
# APIs locais (recomendado em DEV)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_AUTH_API_URL=http://localhost:8001/api/v1/auth
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Opcional: Supabase público
NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=public-anon-key

NEXT_PUBLIC_APP_NAME=Imobly
NEXT_PUBLIC_APP_VERSION=1.0.0
NODE_ENV=development

# Alternativa: usar APIs de produção para desenvolvimento com dados reais
# NEXT_PUBLIC_API_URL=https://backend-non0.onrender.com/api/v1
# NEXT_PUBLIC_AUTH_API_URL=https://auth-api-3zxk.onrender.com/api/v1/auth
```

### 4. Inicie os serviços backend

**Importante**: O frontend depende dos serviços backend para funcionar.

```bash
# Em um terminal separado, inicie o Backend (porta 8000)
cd ../backend
# Siga as instruções do README do backend

# Em outro terminal, inicie a Auth API (porta 8001)
cd ../auth-api
# Siga as instruções do README da auth-api
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

- Erro "Failed to fetch" no login: garanta Backend em `localhost:8000` e Auth API em `localhost:8001`; confirme URLs em `.env.local`.
- Porta 3000 em uso (Windows): `netstat -ano | findstr :3000` e finalize o processo se necessário.
## 📄 Licença

Este projeto é propriedade da **Imobly**.

---
**Desenvolvido pela equipe Imobly** • [Organização GitHub](https://github.com/Imobly)
Para documentação completa, acesse: https://imobly.github.io/Documentation/
