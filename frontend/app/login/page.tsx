'use client';

import { useState } from 'react';
import { LoginForm } from '../../components/auth/login-form';
import { RegisterForm } from '../../components/auth/register-form';
import { BrandLogo } from '../../components/auth/brand-logo';
import { AuthShowcase } from '../../components/auth/auth-showcase';

export default function LoginPage() {
  const [isLoginMode, setIsLoginMode] = useState(true);

  const toggleMode = () => {
    setIsLoginMode(!isLoginMode);
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Lado esquerdo — formulário */}
      <div className="flex flex-col justify-center bg-white px-6 py-12 sm:px-12 lg:px-16">
        <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center">
          <BrandLogo className="mb-12 animate-fade-up" />

          {isLoginMode ? (
            <LoginForm onToggleMode={toggleMode} />
          ) : (
            <RegisterForm onToggleMode={toggleMode} />
          )}
        </div>

        <p className="mx-auto mt-10 text-center text-xs text-gray-400">
          &copy; {new Date().getFullYear()} Imobly. Todos os direitos reservados.
        </p>
      </div>

      {/* Lado direito — apresentação */}
      <AuthShowcase />
    </div>
  );
}
