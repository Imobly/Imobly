import useSWR, { mutate as globalMutate } from 'swr'
import { ApiService, handleApiError } from '@/lib/api'
import { ExpenseResponse, ExpenseFilters } from '@/lib/types/api'

// Cache key builder
const EXPENSES_KEY = '/expenses'
const getExpensesKey = (filters?: ExpenseFilters) => {
  // Normaliza: ignora valores vazios e ordena as chaves, para que filtros
  // ausentes / {} / { x: '' } compartilhem a mesma chave de cache (dedupe SWR).
  const entries = filters
    ? Object.entries(filters).filter(([, v]) => v !== undefined && v !== null && v !== '')
    : []
  if (entries.length === 0) return EXPENSES_KEY
  const normalized = Object.fromEntries(entries.sort(([a], [b]) => a.localeCompare(b)))
  return `${EXPENSES_KEY}?${JSON.stringify(normalized)}`
}

interface UseExpensesReturn {
  expenses: ExpenseResponse[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  createExpense: (expense: any) => Promise<ExpenseResponse | null>
  updateExpense: (id: string, expense: any) => Promise<ExpenseResponse | null>
  deleteExpense: (id: string) => Promise<boolean>
}

export function useExpenses(filters?: ExpenseFilters): UseExpensesReturn {
  const key = getExpensesKey(filters)

  const { data, error: swrError, isLoading, mutate } = useSWR<ExpenseResponse[]>(
    key,
    () => ApiService.expenses.getExpenses(filters),
  )

  const invalidateRelated = async () => {
    await mutate()
    await globalMutate((k: string) => typeof k === 'string' && k.startsWith('/dashboard'), undefined, { revalidate: true })
  }

  const createExpense = async (expense: any): Promise<ExpenseResponse | null> => {
    try {
      const newExpense = await ApiService.expenses.createExpense(expense)
      await invalidateRelated()
      return newExpense
    } catch (err) {
      console.error('Erro ao criar despesa:', err)
      throw err
    }
  }

  const updateExpense = async (id: string, expense: any): Promise<ExpenseResponse | null> => {
    try {
      const updatedExpense = await ApiService.expenses.updateExpense(id, expense)
      await invalidateRelated()
      return updatedExpense
    } catch (err) {
      console.error('Erro ao atualizar despesa:', err)
      throw err
    }
  }

  const deleteExpense = async (id: string): Promise<boolean> => {
    try {
      await ApiService.expenses.deleteExpense(id)
      await invalidateRelated()
      return true
    } catch (err) {
      console.error('Erro ao deletar despesa:', err)
      return false
    }
  }

  return {
    expenses: data ?? [],
    loading: isLoading,
    error: swrError ? handleApiError(swrError) : null,
    refetch: async () => { await mutate() },
    createExpense,
    updateExpense,
    deleteExpense,
  }
}

// Hook para buscar uma despesa específica
export function useExpense(id: string) {
  const { data, error: swrError, isLoading } = useSWR<ExpenseResponse>(
    id ? `${EXPENSES_KEY}/${id}` : null,
    () => ApiService.expenses.getExpense(id),
  )

  return {
    expense: data ?? null,
    loading: isLoading,
    error: swrError ? handleApiError(swrError) : null,
  }
}