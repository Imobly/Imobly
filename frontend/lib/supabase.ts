import { createClient, SupabaseClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

/**
 * Singleton Supabase client (unauthenticated).
 * Auth is managed externally (backend issues Supabase JWTs),
 * so we disable auto-session management.
 */
export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: false,
    autoRefreshToken: false,
    detectSessionInUrl: false,
  },
})

/**
 * Cached authenticated client — reused while the token stays the same.
 */
let _authClient: SupabaseClient | null = null
let _lastToken: string | null = null

/**
 * Returns a Supabase client authenticated with the current user's JWT.
 * Instead of setSession (which may fail silently with an empty refresh_token),
 * we create a client whose every request carries the Authorization header.
 * This guarantees that auth.uid() resolves correctly inside RLS policies
 * on storage buckets and tables.
 */
export async function getAuthenticatedClient(): Promise<SupabaseClient> {
  const token = typeof window !== 'undefined'
    ? localStorage.getItem('access_token')
    : null

  if (!token) {
    throw new Error('Usuário não autenticado. Faça login novamente.')
  }

  // Reuse the same client while the token hasn't changed
  if (_authClient && _lastToken === token) {
    return _authClient
  }

  _authClient = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false,
    },
    global: {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  })
  _lastToken = token

  return _authClient
}
