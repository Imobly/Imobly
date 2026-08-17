'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../../lib/contexts/auth';

interface LoginFormProps {
  onToggleMode: () => void;
}

export function LoginForm({ onToggleMode }: LoginFormProps) {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const { login } = useAuth();
  const router = useRouter();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (error) setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      await login(formData);

      const redirectTo = sessionStorage.getItem('redirectAfterLogin') || '/dashboard';
      sessionStorage.removeItem('redirectAfterLogin');
      router.push(redirectTo);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao fazer login');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="animate-fade-up [animation-delay:80ms]">
      <h1 className="text-3xl font-bold tracking-tight text-gray-900">Bem-vindo de volta</h1>
      <p className="mt-2 text-gray-500">Entre com suas credenciais para acessar a plataforma.</p>

      <form onSubmit={handleSubmit} className="mt-9 space-y-5">
        <div>
          <label htmlFor="username" className="mb-1.5 block text-sm font-medium text-gray-700">
            Email ou usuário
          </label>
          <input
            id="username"
            name="username"
            type="text"
            required
            value={formData.username}
            onChange={handleInputChange}
            disabled={isLoading}
            placeholder="seu@email.com ou usuario"
            className="w-full rounded-xl border border-gray-300 px-4 py-3 text-gray-900 placeholder-gray-400 outline-none transition-shadow focus:border-blue-500 focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
        </div>

        <div>
          <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-gray-700">
            Senha
          </label>
          <div className="relative">
            <input
              id="password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              required
              value={formData.password}
              onChange={handleInputChange}
              disabled={isLoading}
              placeholder="Digite sua senha"
              className="w-full rounded-xl border border-gray-300 px-4 py-3 pr-12 text-gray-900 placeholder-gray-400 outline-none transition-shadow focus:border-blue-500 focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-1 text-gray-400 transition-colors hover:text-gray-600"
              aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
              tabIndex={-1}
            >
              {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
            </button>
          </div>
        </div>

        {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-500">{error}</div>}

        <button
          type="submit"
          disabled={isLoading}
          className="w-full rounded-xl bg-blue-600 px-4 py-3 font-semibold text-white shadow-lg shadow-blue-600/25 transition-all hover:bg-blue-700 hover:shadow-blue-600/30 focus:ring-4 focus:ring-blue-200 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="h-4 w-4 animate-spin rounded-full border-b-2 border-white" />
              Entrando...
            </span>
          ) : (
            'Entrar'
          )}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500">
        Não tem uma conta?{' '}
        <button
          onClick={onToggleMode}
          type="button"
          className="font-semibold text-blue-600 transition-colors hover:text-blue-700 hover:underline"
        >
          Criar conta
        </button>
      </p>
    </div>
  );
}
