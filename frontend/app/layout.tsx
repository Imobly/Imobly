import type { Metadata } from 'next'
import { GeistSans } from 'geist/font/sans'
import { GeistMono } from 'geist/font/mono'
import { AuthProvider } from '../lib/contexts/auth'
import { SWRProvider } from '../lib/contexts/swr-provider'
import { Toaster } from 'sonner'
import './globals.css'

export const metadata: Metadata = {
  title: 'Imobly',
  description: 'Sistema de Gestão Imobiliária',
  generator: 'Imobly',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="pt-BR">
      <body className={`font-sans ${GeistSans.variable} ${GeistMono.variable}`}>
        <SWRProvider>
          <AuthProvider>
            {children}
            {/* O `toast` do sonner já era chamado em várias telas, mas sem o
                Toaster montado nada aparecia: a ação dava certo ou errado em
                silêncio. */}
            <Toaster position="top-right" richColors closeButton />
          </AuthProvider>
        </SWRProvider>
      </body>
    </html>
  )
}
