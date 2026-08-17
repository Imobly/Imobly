'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../../lib/contexts/auth';
import { toast } from 'sonner';

interface RegisterFormProps {
  onToggleMode: () => void;
}

const inputClass =
  'w-full rounded-xl border border-gray-300 px-4 py-3 text-gray-900 placeholder-gray-400 outline-none transition-shadow focus:border-blue-500 focus:ring-2 focus:ring-blue-500 disabled:opacity-50';

export function RegisterForm({ onToggleMode }: RegisterFormProps) {
  const [formData, setFormData] = useState({
    name: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const { register } = useAuth();
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

    if (!/^[a-z0-9_]+$/.test(formData.username)) {
      setError('Username deve conter apenas letras minúsculas, números e underscore');
      setIsLoading(false);
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('As senhas não coincidem');
      setIsLoading(false);
      return;
    }

    if (formData.password.length < 6) {
      setError('A senha deve ter pelo menos 6 caracteres');
      setIsLoading(false);
      return;
    }

    try {
      await register({
        name: formData.name,
        username: formData.username,
        email: formData.email,
        password: formData.password,
      });

      toast.success('Conta criada com sucesso! Faça login para continuar.');

      await new Promise((resolve) => setTimeout(resolve, 1500));

      router.push('/login');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar conta');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="animate-fade-up [animation-delay:80ms]">
      <h1 className="text-3xl font-bold tracking-tight text-gray-900">Criar conta</h1>
      <p className="mt-2 text-gray-500">Preencha os dados abaixo para começar a usar a plataforma.</p>

      <form onSubmit={handleSubmit} className="mt-9 space-y-4">
        <div>
          <label htmlFor="name" className="mb-1.5 block text-sm font-medium text-gray-700">
            Nome completo
          </label>
          <input
            id="name"
            name="name"
            type="text"
            required
            value={formData.name}
            onChange={handleInputChange}
            disabled={isLoading}
            placeholder="Seu nome completo"
            className={inputClass}
          />
        </div>

        <div>
          <label htmlFor="username" className="mb-1.5 block text-sm font-medium text-gray-700">
            Nome de usuário
          </label>
          <input
            id="username"
            name="username"
            type="text"
            required
            value={formData.username}
            onChange={handleInputChange}
            disabled={isLoading}
            pattern="[a-z0-9_]+"
            title="Apenas letras minúsculas, números e underscore"
            placeholder="usuario_123"
            className={inputClass}
          />
          <p className="mt-1 text-xs text-gray-500">Apenas letras minúsculas, números e underscore (_)</p>
        </div>

        <div>
          <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-gray-700">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            value={formData.email}
            onChange={handleInputChange}
            disabled={isLoading}
            placeholder="seu@email.com"
            className={inputClass}
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
              minLength={6}
              value={formData.password}
              onChange={handleInputChange}
              disabled={isLoading}
              placeholder="Mínimo 6 caracteres"
              className={`${inputClass} pr-12`}
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

        <div>
          <label htmlFor="confirmPassword" className="mb-1.5 block text-sm font-medium text-gray-700">
            Confirmar senha
          </label>
          <div className="relative">
            <input
              id="confirmPassword"
              name="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              required
              minLength={6}
              value={formData.confirmPassword}
              onChange={handleInputChange}
              disabled={isLoading}
              placeholder="Digite a senha novamente"
              className={`${inputClass} pr-12`}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-1 text-gray-400 transition-colors hover:text-gray-600"
              aria-label={showConfirmPassword ? 'Ocultar senha' : 'Mostrar senha'}
              tabIndex={-1}
            >
              {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
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
              Criando conta...
            </span>
          ) : (
            'Criar conta'
          )}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500">
        Já tem uma conta?{' '}
        <button
          onClick={onToggleMode}
          type="button"
          className="font-semibold text-blue-600 transition-colors hover:text-blue-700 hover:underline"
        >
          Entrar
        </button>
      </p>
    </div>
  );
}
