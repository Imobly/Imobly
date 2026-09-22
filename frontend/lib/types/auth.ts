export interface User {
  /** Id da tabela local (ex: "2") — usar em rotas da API. */
  id: string;
  email: string;
  name: string;
  created_at?: string;
  updated_at?: string;
  /**
   * UID do Supabase Auth — é o que `auth.uid()` devolve dentro das policies
   * de RLS, e portanto o único valor válido como primeira pasta no caminho
   * dos uploads. Opcional porque sessões em cache anteriores à sua
   * introdução não o têm; nesse caso o upload falha com aviso pedindo novo
   * login, em vez de gravar em pasta errada.
   */
  supabase_uid?: string;
}

export interface LoginRequest {
  username: string; // Can be email or username
  password: string;
}

export interface RegisterRequest {
  name: string;
  username: string;
  email: string;
  password: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface AuthError {
  detail: string;
  status_code?: number;
}

export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  changePassword: (data: ChangePasswordRequest) => Promise<void>;
  updateUser: (userData: { full_name?: string }) => Promise<User>;
}