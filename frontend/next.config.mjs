/** @type {import('next').NextConfig} */
const nextConfig = {
  // Build configuration
  output: 'standalone', // Produce .next/standalone for Docker runtime
  
  // Image optimization
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
      },
      {
        protocol: 'https',
        hostname: '*.onrender.com',
      },
      {
        protocol: 'https',
        hostname: '*.supabase.co',
      },
    ],
  },
  
  // API Rewrites - only in development
  async rewrites() {
    if (process.env.NODE_ENV === 'production') {
      return []
    }
    
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://imobly-backend:8000/api/v1/:path*',
      },
    ]
  },
  
  // Build settings
  //
  // As duas checagens estavam DESLIGADAS. Num código gerado por IA, o
  // compilador TypeScript é a principal defesa contra props alucinadas e
  // contratos de API que não batem — e era exatamente ele que estava mudo.
  // Ao reativar, apareceram 13 erros reais em 7 arquivos; um deles era um bug
  // visível: a UI lia `tenant.status`, campo que a API não devolvia, e todo
  // inquilino era exibido como "inativo".
  //
  // Mantenha ligado. Se um erro travar o build, corrija o tipo — não volte a
  // desligar a checagem.
  eslint: {
    ignoreDuringBuilds: false,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  
  // Environment variables available to the client
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || (process.env.NODE_ENV === 'production' ? 'http://localhost:8000/api/v1' : '/api/v1'),
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  },
}

export default nextConfig