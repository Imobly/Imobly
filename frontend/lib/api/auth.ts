import { apiClient } from '@/lib/api/client'
import { LoginRequest, RegisterRequest, ChangePasswordRequest, User } from '@/lib/types/auth'

// Caminho relativo ao baseURL do apiClient (NEXT_PUBLIC_API_URL + /auth).
// Manter relativo evita requests para a porta errada (8001 vs 8000).
const AUTH_BASE = '/auth'

// Forma do payload retornado pelo backend em /auth/me e /auth/login.
interface TokenResponse {
  access_token: string
  token_type: string
  refresh_token?: string | null
}
interface UserResponse {
  id: string | number
  email: string
  username?: string | null
  full_name?: string | null
  created_at?: string
  updated_at?: string | null
}

function toUser(data: UserResponse): User {
  return {
    id: String(data.id),
    email: data.email,
    name: data.full_name || data.username || data.email,
    created_at: data.created_at,
    updated_at: data.updated_at ?? undefined,
  }
}

/** Autentica via /auth/login (JSON), guarda token e perfil, e retorna o usuário. */
export async function login(credentials: LoginRequest): Promise<User> {
  const tokenData = await apiClient.post<TokenResponse>(`${AUTH_BASE}/login`, {
    username: credentials.username, // pode ser email ou username
    password: credentials.password,
  })

  if (!tokenData?.access_token) {
    throw { detail: 'Resposta de login inválida' }
  }

  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', tokenData.access_token)
  }

  // Busca o perfil do usuário (token já é injetado pelo interceptor do apiClient)
  const user = toUser(await apiClient.get<UserResponse>(`${AUTH_BASE}/me`))
  if (typeof window !== 'undefined') {
    localStorage.setItem('user', JSON.stringify(user))
  }
  return user
}

/** Registra um novo usuário (sem auto-login — o fluxo força o login em seguida). */
export async function register(userData: RegisterRequest): Promise<void> {
  await apiClient.post(`${AUTH_BASE}/register`, {
    email: userData.email,
    username: userData.username,
    full_name: userData.name,
    password: userData.password,
  })
}

/** Altera a senha do usuário autenticado. */
export async function changePassword(data: ChangePasswordRequest): Promise<void> {
  await apiClient.post(`${AUTH_BASE}/change-password`, {
    current_password: data.old_password,
    new_password: data.new_password,
  })
}

/** Atualiza nome/email do usuário e sincroniza o cache local. */
export async function updateUser(userData: { email?: string; full_name?: string }): Promise<User> {
  const user = toUser(await apiClient.put<UserResponse>(`${AUTH_BASE}/me`, userData))
  if (typeof window !== 'undefined') {
    localStorage.setItem('user', JSON.stringify(user))
  }
  return user
}

/** Retorna o usuário atual a partir do backend; em erro de rede, cai no cache local. */
export async function getCurrentUser(): Promise<User | null> {
  if (typeof window === 'undefined' || !localStorage.getItem('access_token')) {
    return null
  }
  try {
    const user = toUser(await apiClient.get<UserResponse>(`${AUTH_BASE}/me`))
    localStorage.setItem('user', JSON.stringify(user))
    return user
  } catch {
    // O interceptor do apiClient já trata 401 (limpa token + redireciona).
    return getStoredUser()
  }
}

export async function logout(): Promise<void> {
  if (typeof window === 'undefined') return
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
}

export function isAuthenticated(): boolean {
  return typeof window !== 'undefined' && !!localStorage.getItem('access_token')
}

export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null
  const raw = localStorage.getItem('user')
  if (!raw) return null
  try {
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}
