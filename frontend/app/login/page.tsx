'use client';

import { useState } from 'react';
import Image from 'next/image';
import { LoginForm } from '../../components/auth/login-form';
import { RegisterForm } from '../../components/auth/register-form';

export default function LoginPage() {
  const [isLoginMode, setIsLoginMode] = useState(true);

  const toggleMode = () => {
    setIsLoginMode(!isLoginMode);
  };

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-2">
      {/* Left side - Hero Image */}
      <div className="hidden lg:block relative bg-blue-50">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-blue-100" />
        
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-20">
          <div className="h-full w-full bg-gradient-to-br from-white/10 to-transparent" 
               style={{
                 backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.15) 1px, transparent 0)',
                 backgroundSize: '20px 20px'
               }} 
          />
        </div>
        
        {/* Content */}
        <div className="relative z-10 flex flex-col items-center justify-center h-full p-12 text-center">
          <div className="max-w-lg">
            <div className="mb-8 flex justify-center">
              <div className="bg-white p-8 rounded-3xl shadow-xl border-6 border-gray-900/70">
                <Image
                  src="/logo.svg"
                  alt="Imobly Logo"
                  width={160}
                  height={160}
                  className=""
                />
              </div>
            </div>
            
            <h1 className="text-4xl font-bold text-white mb-6">
              Gerencie seu negócio imobiliário
            </h1>
            
            <p className="text-xl text-gray-600 mb-8 leading-relaxed">
              Controle completo de propriedades, inquilinos, pagamentos e despesas em uma plataforma integrada.
            </p>
            
            <div className="grid grid-cols-2 gap-3 max-w-md mx-auto">
              <div className="bg-white p-3 rounded-lg text-center shadow-md border border-gray-200">
                <div className="flex items-center justify-center mb-1">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div className="text-sm font-semibold text-blue-700">Relatórios</div>
              </div>
              <div className="bg-white p-3 rounded-lg text-center shadow-md border border-gray-200">
                <div className="flex items-center justify-center mb-1">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                  </svg>
                </div>
                <div className="text-sm font-semibold text-green-700">Pagamentos</div>
              </div>
              <div className="bg-white p-3 rounded-lg text-center shadow-md border border-gray-200">
                <div className="flex items-center justify-center mb-1">
                  <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-2m-2 0H7m5 0v-9a2 2 0 012-2h2a2 2 0 012 2v9" />
                  </svg>
                </div>
                <div className="text-sm font-semibold text-orange-700">Propriedades</div>
              </div>
              <div className="bg-white p-3 rounded-lg text-center shadow-md border border-gray-200">
                <div className="flex items-center justify-center mb-1">
                  <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <div className="text-sm font-semibold text-yellow-700">Inquilinos</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right side - Form */}
      <div className="flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="text-center mb-10">
            <div className="flex justify-center">
              <Image
                src="/logo-icon.svg"
                alt="Imobly"
                width={120}
                height={120}
                className="drop-shadow-lg"
              />
            </div>
          </div>

          {/* Form */}
          {isLoginMode ? (
            <LoginForm onToggleMode={toggleMode} />
          ) : (
            <RegisterForm onToggleMode={toggleMode} />
          )}
        </div>
      </div>
    </div>
  );
}