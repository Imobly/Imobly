"use client"

import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function RegisterPlaceholder() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="max-w-md w-full bg-white border rounded-xl shadow-sm p-8 space-y-4">
        <h1 className="text-xl font-semibold">Cadastro</h1>
        <p className="text-sm text-gray-600">
          O auto-cadastro ainda não está disponível. Entre em contato com o suporte para criar sua conta inicial.
        </p>
        <Button asChild className="w-full bg-blue-600 hover:bg-blue-700">
          <Link href="/login">Voltar para Login</Link>
        </Button>
      </div>
    </div>
  )
}
