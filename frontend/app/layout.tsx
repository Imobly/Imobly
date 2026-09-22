import type { Metadata } from 'next'
import { GeistMono } from 'geist/font/mono'
import { Bricolage_Grotesque, Plus_Jakarta_Sans } from 'next/font/google'
import { AuthProvider } from '../lib/contexts/auth'
import { SWRProvider } from '../lib/contexts/swr-provider'
import { Toaster } from 'sonner'
import './globals.css'

// Duas faces, papéis separados: a display carrega os títulos de página e os
// valores em destaque; a de interface carrega todo o resto. Geist Sans saiu
// porque é indistinguível do Inter padrão de template.
const jakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-jakarta',
  display: 'swap',
})

const bricolage = Bricolage_Grotesque({
  subsets: ['latin'],
  weight: ['600', '700'],
  variable: '--font-bricolage',
  display: 'swap',
})

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
      <body className={`font-sans ${jakarta.variable} ${bricolage.variable} ${GeistMono.variable}`}>
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
