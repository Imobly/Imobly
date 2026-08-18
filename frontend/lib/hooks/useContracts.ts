import useSWR, { mutate as globalMutate } from 'swr'
import { ApiService, handleApiError } from '@/lib/api'
import { ContractResponse, ContractCreate, ContractFilters } from '@/lib/types/api'

// Cache key builder
const CONTRACTS_KEY = '/contracts'
const getContractsKey = (filters?: ContractFilters) => {
  // Normaliza: ignora valores vazios e ordena as chaves, para que filtros
  // ausentes / {} / { x: '' } compartilhem a mesma chave de cache (dedupe SWR).
  const entries = filters
    ? Object.entries(filters).filter(([, v]) => v !== undefined && v !== null && v !== '')
    : []
  if (entries.length === 0) return CONTRACTS_KEY
  const normalized = Object.fromEntries(entries.sort(([a], [b]) => a.localeCompare(b)))
  return `${CONTRACTS_KEY}?${JSON.stringify(normalized)}`
}

interface UseContractsReturn {
  contracts: ContractResponse[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  createContract: (contract: ContractCreate) => Promise<ContractResponse | null>
}

export function useContracts(filters?: ContractFilters): UseContractsReturn {
  const key = getContractsKey(filters)

  const { data, error: swrError, isLoading, mutate } = useSWR<ContractResponse[]>(
    key,
    () => ApiService.contracts.getContracts(filters),
  )

  const createContract = async (contract: ContractCreate): Promise<ContractResponse | null> => {
    try {
      const newContract = await ApiService.contracts.createContract(contract)
      // Revalidar lista de contratos
      await mutate()
      // Também invalidar dashboard
      await globalMutate((k: string) => typeof k === 'string' && k.startsWith('/dashboard'), undefined, { revalidate: true })
      return newContract
    } catch (err) {
      console.error('Erro ao criar contrato:', err)
      throw err
    }
  }

  const refetch = async () => {
    await mutate()
  }

  return {
    contracts: data ?? [],
    loading: isLoading,
    error: swrError ? handleApiError(swrError) : null,
    refetch,
    createContract,
  }
}

// Hook para buscar um contrato específico (ex: ao editar um inquilino vinculado)
export function useContract(id?: number | null) {
  const { data, error: swrError, isLoading } = useSWR<ContractResponse>(
    id ? `${CONTRACTS_KEY}/${id}` : null,
    () => ApiService.contracts.getContract(id as number),
  )

  return {
    contract: data ?? null,
    loading: isLoading,
    error: swrError ? handleApiError(swrError) : null,
  }
}