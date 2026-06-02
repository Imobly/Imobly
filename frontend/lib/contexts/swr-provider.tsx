'use client'

import { SWRConfig } from 'swr'
import { ReactNode } from 'react'

interface SWRProviderProps {
  children: ReactNode
}

export function SWRProvider({ children }: SWRProviderProps) {
  return (
    <SWRConfig
      value={{
        revalidateOnFocus: false,       // Não refaz fetch ao focar na aba
        revalidateOnReconnect: true,     // Refaz fetch ao reconectar internet
        dedupingInterval: 5000,          // Deduplicar chamadas idênticas em 5s
        errorRetryCount: 2,              // Máximo 2 retentativas em caso de erro
        keepPreviousData: true,          // Mantém dados anteriores enquanto revalida
        revalidateIfStale: false,        // Não revalida automaticamente dados stale
        shouldRetryOnError: (err: any) => {
          // Não retentar em erros de autenticação/autorização
          if (err?.response?.status === 401 || err?.response?.status === 403) {
            return false
          }
          return true
        },
      }}
    >
      {children}
    </SWRConfig>
  )
}
