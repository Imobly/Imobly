# Guia — Página de Login (split-screen)

Guia autossuficiente para reconstruir **exatamente** a página de login desta
aplicação em outro projeto React + Tailwind. Inclui dependências, fontes, código
completo dos componentes e os pontos onde você troca **paleta, imagem e textos**.

> Layout: tela dividida em duas colunas.
> **Esquerda** (branca) = formulário de login + logo + link de cadastro.
> **Direita** (escura) = painel de apresentação com fundo "tinta na água" (CSS/SVG)
> e, opcionalmente, uma foto sua por cima. Sem paginação e sem login social.

---

## 1. Pré-requisitos / dependências

A página assume uma stack **React 18 + TypeScript + Vite + TailwindCSS**. Pacotes:

```bash
npm install react-router-dom react-hot-toast react-icons
# Tailwind (se ainda não tiver):
npm install -D tailwindcss postcss autoprefixer
```

Você também precisa de um **contexto de autenticação** que exponha `login`,
`register`, `user` e `loading`. Veja o "contrato" mínimo na Seção 7 — se o seu
projeto já tem auth, basta adaptar os imports.

---

## 2. Fontes (padrão da aplicação)

A identidade usa **Sora** (títulos / display) + **Inter** (corpo).

### 2.1. Importar no `index.html`

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Sora:wght@400;500;600;700;800&display=swap"
  rel="stylesheet"
/>
```

### 2.2. `src/index.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

@layer base {
  html {
    @apply bg-gray-50 text-gray-900;
  }

  /* Títulos seguem o padrão de display (Sora); o corpo permanece em Inter. */
  h1,
  h2,
  h3,
  h4 {
    font-family: 'Sora', 'Inter', system-ui, sans-serif;
  }
}
```

---

## 3. Configuração do Tailwind (`tailwind.config.js`)

Adicione a paleta `primary`, a família `display` e as animações usadas no load.

> 🎨 **TROQUE A PALETA AQUI.** Os tons `primary.*` definem a cor da marca em toda
> a página (botões, foco, painel direito). Substitua pelos tons da sua marca
> mantendo a escala 50→900 (do mais claro ao mais escuro). O exemplo abaixo é um
> azul; troque pelos seus HEX.

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // 🎨 PALETA DA MARCA — troque estes HEX
        primary: {
          50:  '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
      },
      fontFamily: {
        display: ['Sora', 'Inter', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'ink-drift': {
          '0%, 100%': { transform: 'translate3d(0, 0, 0) scale(1)' },
          '50%': { transform: 'translate3d(-2%, 1.5%, 0) scale(1.06)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.6s cubic-bezier(0.22, 1, 0.36, 1) both',
        'ink-drift': 'ink-drift 22s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
```

> Se você usa Tailwind v4 (config via CSS `@theme`), traduza estas chaves para a
> sintaxe equivalente — os nomes (`primary`, `font-display`, `animate-fade-up`,
> `animate-ink-drift`) precisam continuar existindo.

---

## 4. Estrutura de arquivos

```
src/
├── components/
│   └── auth/
│       ├── BrandLogo.tsx       # símbolo + nome da marca
│       ├── AuthShowcase.tsx    # painel direito (fundo tinta + textos)
│       ├── LoginForm.tsx       # formulário de login
│       └── RegisterModal.tsx   # modal de cadastro
└── pages/
    └── LoginPage.tsx           # compõe os 4 acima

public/
└── login-bg.jpg               # (opcional) sua foto de fundo do painel direito
```

---

## 5. Código dos componentes

### 5.1. `src/components/auth/BrandLogo.tsx`

> ✏️ **TROQUE:** nome (`Auto Tuss`), subtítulo (`by Bluelephant`) e o ícone SVG
> pela logo da sua marca.

```tsx
type BrandLogoProps = {
  /** Cor do texto da marca. Use "light" sobre fundos escuros. */
  variant?: 'dark' | 'light'
  className?: string
}

/**
 * Marca da aplicação: símbolo + wordmark.
 */
export default function BrandLogo({ variant = 'dark', className = '' }: BrandLogoProps) {
  const text = variant === 'light' ? 'text-white' : 'text-gray-900'
  const sub = variant === 'light' ? 'text-white/60' : 'text-gray-400'

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <span className="relative inline-flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary-400 via-primary-600 to-primary-800 shadow-lg shadow-primary-600/30">
        <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5 text-white">
          <path
            d="M7 3.5h6.5L18 8v9.5A2 2 0 0 1 16 19.5H7A2 2 0 0 1 5 17.5v-12A2 2 0 0 1 7 3.5Z"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
          <path d="M13 3.5V8h4.5" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
          <path
            d="M8 13.2l1.8 1.8 2-2.6 1.6 2.1L15 13"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <span className="flex flex-col leading-none">
        {/* ✏️ TROQUE o nome e o subtítulo da marca */}
        <span className={`font-display text-lg font-bold tracking-tight ${text}`}>Auto Tuss</span>
        <span className={`text-[11px] font-medium tracking-wide ${sub}`}>by Bluelephant</span>
      </span>
    </div>
  )
}
```

### 5.2. `src/components/auth/AuthShowcase.tsx`

O fundo "tinta azul na água" é construído **em camadas de CSS/SVG**, então
funciona sem nenhuma imagem. Se quiser usar uma foto, salve-a em
`public/login-bg.jpg` (a Camada 3 a aplica automaticamente por cima).

> 🎨 **Paleta:** o fundo herda os tons `primary.*` (e alguns HEX explícitos nos
> gradientes da Camada 1 — ajuste-os se mudar muito a cor).
> 🖼️ **Imagem:** troque o caminho `'/login-bg.jpg'` na Camada 3.
> ✏️ **Textos:** título, parágrafo, os 3 cards e o rodapé.

```tsx
/**
 * Painel lateral de apresentação (lado direito do login).
 *
 * Fundo "tinta na água" em camadas:
 *  1. Gradientes radiais (profundidade).
 *  2. Textura orgânica gerada por SVG (feTurbulence) tingida na cor da marca.
 *  3. (Opcional) foto em /public/login-bg.jpg sobreposta com blend.
 */
export default function AuthShowcase() {
  return (
    <div className="relative hidden overflow-hidden bg-primary-900 lg:block">
      {/* Camada 1 — gradientes de profundidade */}
      {/* 🎨 ajuste os HEX para casar com sua paleta */}
      <div
        className="absolute inset-0 animate-ink-drift"
        style={{
          backgroundColor: '#0b1f5c',
          backgroundImage: [
            'radial-gradient(120% 80% at 70% 18%, rgba(96,165,250,0.55) 0%, rgba(37,99,235,0) 55%)',
            'radial-gradient(90% 70% at 20% 12%, rgba(30,64,175,0.85) 0%, rgba(30,64,175,0) 60%)',
            'radial-gradient(120% 90% at 30% 100%, rgba(8,15,45,0.95) 0%, rgba(8,15,45,0) 55%)',
            'radial-gradient(80% 60% at 85% 75%, rgba(59,130,246,0.45) 0%, rgba(59,130,246,0) 60%)',
          ].join(','),
        }}
      />

      {/* Camada 2 — textura de tinta (SVG turbulence tingido) */}
      {/* 🎨 a matriz feColorMatrix define a cor da tinta (R G B na 4ª coluna do alpha) */}
      <svg className="absolute inset-0 h-full w-full opacity-[0.45] mix-blend-soft-light" aria-hidden="true">
        <filter id="ink-texture">
          <feTurbulence type="fractalNoise" baseFrequency="0.012 0.018" numOctaves="4" seed="7" stitchTiles="stitch" />
          <feColorMatrix
            type="matrix"
            values="0 0 0 0 0.04
                    0 0 0 0 0.18
                    0 0 0 0 0.65
                    0 0 0 0.9 0"
          />
        </filter>
        <rect width="100%" height="100%" filter="url(#ink-texture)" />
      </svg>

      {/* Camada 3 — foto opcional (entra automaticamente se o arquivo existir) */}
      {/* 🖼️ TROQUE o caminho da imagem */}
      <div
        className="absolute inset-0 bg-cover bg-center opacity-70 mix-blend-overlay"
        style={{ backgroundImage: "url('/login-bg.jpg')" }}
        aria-hidden="true"
      />

      {/* Vinheta para legibilidade do texto */}
      <div className="absolute inset-0 bg-gradient-to-t from-primary-900/80 via-transparent to-primary-900/20" />

      {/* Grão sutil */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.06]"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
        }}
        aria-hidden="true"
      />

      {/* Conteúdo */}
      <div className="relative z-10 flex h-full flex-col justify-between p-12 xl:p-16">
        {/* ✏️ tagline do topo */}
        <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.25em] text-white/50">
          <span className="h-1.5 w-1.5 rounded-full bg-primary-300" />
          OCR Médico Inteligente
        </div>

        <div className="max-w-md animate-fade-up [animation-delay:120ms]">
          {/* ✏️ título principal */}
          <h2 className="font-display text-4xl font-bold leading-[1.1] text-white xl:text-5xl">
            Da imagem ao código TUSS em segundos.
          </h2>
          {/* ✏️ parágrafo */}
          <p className="mt-5 text-base leading-relaxed text-white/70">
            Extraia procedimentos médicos de guias, laudos e pedidos clínicos e
            receba os códigos TUSS correspondentes automaticamente — com
            precisão e rastreabilidade.
          </p>

          {/* ✏️ os 3 cards de destaque */}
          <div className="mt-10 grid grid-cols-3 gap-4">
            {[
              { value: 'OCR', label: 'Leitura inteligente' },
              { value: 'TUSS', label: 'Mapeamento automático' },
              { value: '24/7', label: 'Sempre disponível' },
            ].map((item) => (
              <div
                key={item.value}
                className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm"
              >
                <div className="font-display text-xl font-bold text-white">{item.value}</div>
                <div className="mt-1 text-[11px] leading-tight text-white/55">{item.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* ✏️ rodapé do painel */}
        <p className="max-w-sm text-sm text-white/60">
          Envie seus documentos e deixe a plataforma cuidar da codificação para você.
        </p>
      </div>
    </div>
  )
}
```

### 5.3. `src/components/auth/LoginForm.tsx`

Inclui o toggle de mostrar/ocultar senha e os reveals escalonados (`fade-up`).

> ✏️ **TROQUE:** saudação (`Bem-vindo de volta`) e subtítulo.
> 🔌 **Auth:** usa `useAuth().login(email, password)` — adapte ao seu contexto.

```tsx
import { useState, type FormEvent } from 'react'
import toast from 'react-hot-toast'
import { HiOutlineEye, HiOutlineEyeOff } from 'react-icons/hi'
import { useAuth } from '../../contexts/AuthContext'
import BrandLogo from './BrandLogo'

type LoginFormProps = {
  onRegister: () => void
}

export default function LoginForm({ onRegister }: LoginFormProps) {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await login(email, password)
      toast.success('Login realizado com sucesso')
    } catch {
      toast.error('Email ou senha incorretos')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex w-full max-w-sm flex-col">
      <BrandLogo className="mb-12 animate-fade-up" />

      <div className="animate-fade-up [animation-delay:80ms]">
        {/* ✏️ saudação + subtítulo */}
        <h1 className="font-display text-3xl font-bold tracking-tight text-gray-900">
          Bem-vindo de volta <span className="inline-block">👋</span>
        </h1>
        <p className="mt-2 text-gray-500">Entre com suas credenciais para acessar a plataforma.</p>
      </div>

      <form onSubmit={handleSubmit} className="mt-9 space-y-5 animate-fade-up [animation-delay:160ms]">
        <div>
          <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-gray-700">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-xl border border-gray-300 px-4 py-3 text-gray-900 placeholder-gray-400 outline-none transition-shadow focus:border-primary-500 focus:ring-2 focus:ring-primary-500"
            placeholder="seu@email.com"
          />
        </div>

        <div>
          <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-gray-700">
            Senha
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-gray-300 px-4 py-3 pr-12 text-gray-900 placeholder-gray-400 outline-none transition-shadow focus:border-primary-500 focus:ring-2 focus:ring-primary-500"
              placeholder="Sua senha"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-1 text-gray-400 transition-colors hover:text-gray-600"
              aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
            >
              {showPassword ? (
                <HiOutlineEyeOff className="h-5 w-5" />
              ) : (
                <HiOutlineEye className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-xl bg-primary-600 px-4 py-3 font-semibold text-white shadow-lg shadow-primary-600/25 transition-all hover:bg-primary-700 hover:shadow-primary-600/30 focus:ring-4 focus:ring-primary-200 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? (
            <span className="flex items-center justify-center gap-2">
              <span className="h-4 w-4 animate-spin rounded-full border-b-2 border-white" />
              Entrando...
            </span>
          ) : (
            'Entrar'
          )}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500 animate-fade-up [animation-delay:240ms]">
        Ainda não tem conta?{' '}
        <button
          onClick={onRegister}
          className="font-semibold text-primary-600 transition-colors hover:text-primary-700 hover:underline"
        >
          Cadastre-se
        </button>
      </p>
    </div>
  )
}
```

### 5.4. `src/components/auth/RegisterModal.tsx`

> 🔌 **Auth:** usa `useAuth().register(nome, email, password)`.
> Se a outra aplicação não tiver cadastro, remova este arquivo e o botão
> "Cadastre-se" do `LoginForm`.

```tsx
import { useState, type FormEvent } from 'react'
import toast from 'react-hot-toast'
import { HiOutlineX } from 'react-icons/hi'
import { useAuth } from '../../contexts/AuthContext'

const inputClass =
  'w-full rounded-xl border border-gray-300 px-4 py-2.5 text-gray-900 placeholder-gray-400 outline-none transition-shadow focus:border-primary-500 focus:ring-2 focus:ring-primary-500'

export default function RegisterModal({ onClose }: { onClose: () => void }) {
  const { register } = useAuth()
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (password !== confirmPassword) {
      toast.error('As senhas não coincidem')
      return
    }
    if (password.length < 6) {
      toast.error('A senha deve ter no mínimo 6 caracteres')
      return
    }
    setSubmitting(true)
    try {
      await register(nome, email, password)
      toast.success('Conta criada com sucesso!')
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      toast.error(detail || 'Erro ao criar conta')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-primary-950/50 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl animate-fade-up"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
          aria-label="Fechar"
        >
          <HiOutlineX className="h-5 w-5" />
        </button>

        <h2 className="font-display text-xl font-bold text-gray-900">Criar conta</h2>
        <p className="mb-6 mt-1 text-sm text-gray-500">Preencha os dados para se cadastrar</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="reg-nome" className="mb-1 block text-sm font-medium text-gray-700">
              Nome
            </label>
            <input
              id="reg-nome"
              type="text"
              required
              minLength={2}
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              className={inputClass}
              placeholder="Seu nome completo"
            />
          </div>

          <div>
            <label htmlFor="reg-email" className="mb-1 block text-sm font-medium text-gray-700">
              Email
            </label>
            <input
              id="reg-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass}
              placeholder="seu@email.com"
            />
          </div>

          <div>
            <label htmlFor="reg-password" className="mb-1 block text-sm font-medium text-gray-700">
              Senha
            </label>
            <input
              id="reg-password"
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
              placeholder="Mínimo 6 caracteres"
            />
          </div>

          <div>
            <label htmlFor="reg-confirm" className="mb-1 block text-sm font-medium text-gray-700">
              Confirmar senha
            </label>
            <input
              id="reg-confirm"
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className={inputClass}
              placeholder="Repita a senha"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-xl bg-primary-600 px-4 py-2.5 font-semibold text-white transition-all hover:bg-primary-700 focus:ring-4 focus:ring-primary-200 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? (
              <span className="flex items-center justify-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-b-2 border-white" />
                Criando conta...
              </span>
            ) : (
              'Cadastrar'
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
```

### 5.5. `src/pages/LoginPage.tsx`

Compõe tudo no grid 2 colunas. Redireciona se já estiver logado.

> ✏️ **TROQUE:** rota de destino (`/upload`) e o texto de copyright.

```tsx
import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import LoginForm from '../components/auth/LoginForm'
import RegisterModal from '../components/auth/RegisterModal'
import AuthShowcase from '../components/auth/AuthShowcase'

export default function LoginPage() {
  const { user, loading } = useAuth()
  const [showRegister, setShowRegister] = useState(false)

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-b-2 border-primary-500" />
      </div>
    )
  }

  // ✏️ rota de destino pós-login
  if (user) return <Navigate to="/upload" />

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Lado esquerdo — formulário */}
      <div className="flex flex-col justify-center bg-white px-6 py-12 sm:px-12 lg:px-16">
        <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center">
          <LoginForm onRegister={() => setShowRegister(true)} />
        </div>
        {/* ✏️ copyright */}
        <p className="mx-auto mt-10 text-center text-xs text-gray-400">
          &copy; {new Date().getFullYear()} Bluelephant. Todos os direitos reservados.
        </p>
      </div>

      {/* Lado direito — apresentação */}
      <AuthShowcase />

      {showRegister && <RegisterModal onClose={() => setShowRegister(false)} />}
    </div>
  )
}
```

---

## 6. Registrar a rota

No seu router (ex.: `App.tsx`):

```tsx
import LoginPage from './pages/LoginPage'
// ...
<Route path="/login" element={<LoginPage />} />
```

E garanta que `<Toaster />` do `react-hot-toast` esteja montado uma vez na raiz
(ex.: em `main.tsx` ou `App.tsx`):

```tsx
import { Toaster } from 'react-hot-toast'
// ...
<Toaster position="top-right" />
```

---

## 7. Contrato do contexto de autenticação

Os componentes importam `useAuth` de `../contexts/AuthContext`. O hook precisa
expor, no mínimo:

```ts
type AuthContextValue = {
  user: User | null                 // null = não logado
  loading: boolean                  // true enquanto verifica a sessão
  login: (email: string, password: string) => Promise<void>
  register: (nome: string, email: string, password: string) => Promise<void>
}
```

- `login`/`register` devem **lançar** (throw) em caso de erro — os componentes
  capturam e exibem um toast.
- Se sua aplicação já tem auth com nomes diferentes, basta ajustar os imports e
  as chamadas dentro de `LoginForm`/`RegisterModal`.

---

## 8. Checklist de customização para a nova aplicação

| O quê | Onde |
|------|------|
| 🎨 **Paleta da marca** (`primary.50→900`) | `tailwind.config.js` |
| 🎨 HEX dos gradientes do painel | `AuthShowcase.tsx` — Camada 1 |
| 🎨 Cor da tinta SVG (`feColorMatrix`) | `AuthShowcase.tsx` — Camada 2 |
| 🖼️ **Foto do painel direito** | salvar em `public/login-bg.jpg` (ou trocar o caminho na Camada 3) |
| ✏️ Nome + subtítulo + ícone da marca | `BrandLogo.tsx` |
| ✏️ Tagline, título, parágrafo, 3 cards, rodapé | `AuthShowcase.tsx` — bloco "Conteúdo" |
| ✏️ Saudação e subtítulo do form | `LoginForm.tsx` |
| ✏️ Rota pós-login + copyright | `LoginPage.tsx` |
| 🔌 Integração de auth | `LoginForm.tsx`, `RegisterModal.tsx`, contexto |
| 🔤 Fontes | `index.html` + `index.css` + `tailwind.config.js` |

### Notas sobre a imagem do painel direito
- Funciona **sem** imagem (o fundo CSS/SVG já é completo).
- Para usar foto: orientação **retrato** (mais alta que larga) funciona melhor,
  pois o painel ocupa metade da tela em altura cheia. Formato `.jpg`/`.webp`.
- A foto entra com `mix-blend-overlay` + `opacity-70`, então ela se mistura à cor
  do fundo. Para deixá-la mais nítida/dominante, aumente a opacidade ou troque o
  blend mode na Camada 3 do `AuthShowcase.tsx`.

---

## 9. Detalhes de design (para manter a identidade)

- **Layout:** `grid lg:grid-cols-2`, altura `min-h-screen`. Abaixo de `lg` o
  painel direito some (`hidden lg:block`) e o formulário ocupa a tela toda.
- **Tipografia:** títulos em `font-display` (Sora, peso 700/800); corpo em Inter.
- **Botão primário:** `bg-primary-600` com sombra colorida (`shadow-primary-600/25`)
  e estado de foco com anel (`focus:ring-4 focus:ring-primary-200`).
- **Cantos:** inputs e botões `rounded-xl`; cards do painel `rounded-2xl`.
- **Movimento:** uma única coreografia de entrada — `animate-fade-up` com delays
  escalonados (`[animation-delay:80ms]`, `160ms`, `240ms`) para logo → título →
  form → link. O fundo respira lentamente com `animate-ink-drift` (22s).
- **Profundidade do painel:** 5 camadas empilhadas (gradientes → textura de tinta
  → foto opcional → vinheta → grão) criam atmosfera em vez de cor chapada.
- **Acessibilidade:** `aria-label` no toggle de senha e no fechar do modal;
  elementos decorativos com `aria-hidden`.
```
