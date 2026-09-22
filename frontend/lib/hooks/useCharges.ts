import useSWR, { mutate as globalMutate } from 'swr'
import { ApiService } from '@/lib/api'
import type {
  AgingReport,
  Charge,
  ChargeFilters,
  DelinquencyRow,
  PaymentEntryInput,
  TenantLedger,
} from '@/lib/types/charge'

const CHARGES_KEY = '/charges'

const getChargesKey = (filters?: ChargeFilters) => {
  // Mesma normalização usada em usePayments: filtros ausentes, `{}` e
  // `{ x: '' }` precisam compartilhar a mesma chave, senão o SWR mantém
  // caches paralelos da mesma lista e a tela mostra números diferentes
  // conforme a ordem em que os componentes montaram.
  const entries = filters
    ? Object.entries(filters).filter(([, v]) => v !== undefined && v !== null && v !== '')
    : []
  if (entries.length === 0) return CHARGES_KEY
  const normalized = Object.fromEntries(entries.sort(([a], [b]) => a.localeCompare(b)))
  return `${CHARGES_KEY}?${JSON.stringify(normalized)}`
}

/**
 * Invalida tudo que depende de dinheiro.
 *
 * Um recebimento muda o saldo da cobrança, o aging, o KPI do painel e o badge
 * do inquilino. Revalidar só a lista de cobranças deixa o resto da tela
 * exibindo números velhos — e, num painel de inadimplência, número velho é
 * indistinguível de número errado.
 */
const invalidarDependentes = async () => {
  await globalMutate(
    (k: string) =>
      typeof k === 'string' &&
      (k.startsWith('/charges') ||
        k.startsWith('/payments') ||
        k.startsWith('/dashboard') ||
        k.startsWith('/tenants')),
    undefined,
    { revalidate: true }
  )
}

interface UseChargesReturn {
  charges: Charge[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  addEntry: (chargeId: number, entry: PaymentEntryInput) => Promise<boolean>
  settle: (chargeId: number, paymentDate?: string, method?: string) => Promise<boolean>
  cancel: (chargeId: number) => Promise<boolean>
  generate: (competencia?: string) => Promise<number | null>
}

export function useCharges(filters?: ChargeFilters): UseChargesReturn {
  const key = getChargesKey(filters)

  const { data, error: swrError, isLoading, mutate } = useSWR<Charge[]>(key, () =>
    ApiService.charges.getCharges(filters)
  )

  const executar = async <T>(acao: () => Promise<T>, rotulo: string): Promise<T | null> => {
    try {
      const resultado = await acao()
      await mutate()
      await invalidarDependentes()
      return resultado
    } catch (err) {
      console.error(`Erro ao ${rotulo}:`, err)
      return null
    }
  }

  return {
    charges: data || [],
    loading: isLoading,
    error: swrError ? String(swrError.message || swrError) : null,
    refetch: async () => {
      await mutate()
    },
    addEntry: async (chargeId, entry) =>
      (await executar(() => ApiService.charges.addEntry(chargeId, entry), 'registrar recebimento')) !==
      null,
    settle: async (chargeId, paymentDate, method) =>
      (await executar(
        () => ApiService.charges.settle(chargeId, paymentDate, method),
        'quitar cobrança'
      )) !== null,
    cancel: async (chargeId) =>
      (await executar(() => ApiService.charges.cancel(chargeId), 'cancelar cobrança')) !== null,
    generate: async (competencia) => {
      const resultado = await executar(
        () => ApiService.charges.generate(competencia),
        'gerar cobranças'
      )
      return resultado ? resultado.created : null
    },
  }
}

export function useAging() {
  const { data, error, isLoading, mutate } = useSWR<AgingReport>('/charges/aging', () =>
    ApiService.charges.getAging()
  )
  return {
    aging: data,
    loading: isLoading,
    error: error ? String(error.message || error) : null,
    refetch: mutate,
  }
}

export function useDelinquency(limit = 50) {
  const { data, error, isLoading, mutate } = useSWR<DelinquencyRow[]>(
    `/charges/delinquency?limit=${limit}`,
    () => ApiService.charges.getDelinquency(limit)
  )
  return {
    rows: data || [],
    loading: isLoading,
    error: error ? String(error.message || error) : null,
    refetch: mutate,
  }
}

export function useTenantLedger(tenantId: number | null) {
  const { data, error, isLoading, mutate } = useSWR<TenantLedger>(
    tenantId ? `/tenants/${tenantId}/ledger` : null,
    () => ApiService.charges.getTenantLedger(tenantId as number)
  )
  return {
    ledger: data,
    loading: isLoading,
    error: error ? String(error.message || error) : null,
    refetch: mutate,
  }
}
