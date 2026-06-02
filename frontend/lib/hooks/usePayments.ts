import useSWR, { mutate as globalMutate } from 'swr'
import { ApiService, handleApiError } from '@/lib/api'
import { PaymentResponse, PaymentFilters } from '@/lib/types/api'

// Cache key builder
const PAYMENTS_KEY = '/payments'
const getPaymentsKey = (filters?: PaymentFilters) => {
  // Normaliza: ignora valores vazios e ordena as chaves, para que filtros
  // ausentes / {} / { x: '' } compartilhem a mesma chave de cache (dedupe SWR).
  const entries = filters
    ? Object.entries(filters).filter(([, v]) => v !== undefined && v !== null && v !== '')
    : []
  if (entries.length === 0) return PAYMENTS_KEY
  const normalized = Object.fromEntries(entries.sort(([a], [b]) => a.localeCompare(b)))
  return `${PAYMENTS_KEY}?${JSON.stringify(normalized)}`
}

interface UsePaymentsReturn {
  payments: PaymentResponse[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  confirmPayment: (id: number, data?: any) => Promise<boolean>
  createPayment: (payment: any) => Promise<PaymentResponse | null>
  deletePayment: (id: number) => Promise<boolean>
}

export function usePayments(filters?: PaymentFilters): UsePaymentsReturn {
  const key = getPaymentsKey(filters)

  const { data, error: swrError, isLoading, mutate } = useSWR<PaymentResponse[]>(
    key,
    () => ApiService.payments.getPayments(filters),
  )

  const invalidateRelated = async () => {
    await mutate()
    await globalMutate((k: string) => typeof k === 'string' && k.startsWith('/dashboard'), undefined, { revalidate: true })
  }

  const confirmPayment = async (id: number, confirmData?: any): Promise<boolean> => {
    try {
      await ApiService.payments.confirmPayment(id, confirmData)
      await invalidateRelated()
      return true
    } catch (err) {
      console.error('❌ Erro ao confirmar pagamento:', err)
      return false
    }
  }

  const createPayment = async (payment: any): Promise<PaymentResponse | null> => {
    try {
      const newPayment = await ApiService.payments.createPayment(payment)
      await invalidateRelated()
      return newPayment
    } catch (err) {
      console.error('❌ Erro ao criar pagamento:', err)
      return null
    }
  }

  const deletePayment = async (id: number): Promise<boolean> => {
    try {
      await ApiService.payments.deletePayment(id)
      await invalidateRelated()
      return true
    } catch (err) {
      console.error('❌ Erro ao excluir pagamento:', err)
      return false
    }
  }

  return {
    payments: data ?? [],
    loading: isLoading,
    error: swrError ? handleApiError(swrError) : null,
    refetch: async () => { await mutate() },
    confirmPayment,
    createPayment,
    deletePayment,
  }
}

// Hook para pagamentos em atraso
export function useOverduePayments() {
  const { data, error: swrError, isLoading } = useSWR<PaymentResponse[]>(
    `${PAYMENTS_KEY}/overdue`,
    () => ApiService.payments.getOverduePayments(),
  )

  return {
    overduePayments: data ?? [],
    loading: isLoading,
    error: swrError ? handleApiError(swrError) : null,
  }
}