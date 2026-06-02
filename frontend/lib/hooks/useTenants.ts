import useSWR, { mutate as globalMutate } from 'swr'
import { useMemo } from 'react'
import { ApiService, handleApiError } from '@/lib/api'
import { TenantResponse, TenantFilters, ContractResponse, PropertyResponse } from '@/lib/types/api'

// Cache key builder
const TENANTS_KEY = '/tenants'
const getTenantsKey = (filters?: TenantFilters) => {
  // Normaliza: ignora valores vazios e ordena as chaves, para que filtros
  // ausentes / {} / { x: '' } compartilhem a mesma chave de cache (dedupe SWR).
  const entries = filters
    ? Object.entries(filters).filter(([, v]) => v !== undefined && v !== null && v !== '')
    : []
  if (entries.length === 0) return TENANTS_KEY
  const normalized = Object.fromEntries(entries.sort(([a], [b]) => a.localeCompare(b)))
  return `${TENANTS_KEY}?${JSON.stringify(normalized)}`
}

interface EnrichedTenant extends TenantResponse {
  property_name?: string
  property_address?: string
  rent?: number
  due_day?: number
  contract_start?: string
  contract_end?: string
  status: 'ativo' | 'inativo'
}

interface UseTenantsReturn {
  tenants: EnrichedTenant[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  createTenant: (tenant: any) => Promise<TenantResponse | null>
  updateTenant: (id: number, tenant: any) => Promise<TenantResponse | null>
  deleteTenant: (id: number) => Promise<boolean>
}

export function useTenants(filters?: TenantFilters): UseTenantsReturn {
  const key = getTenantsKey(filters)

  // Fetch tenants
  const { data: tenantsData, error: tenantsError, isLoading: tenantsLoading, mutate: mutateTenants } = useSWR<TenantResponse[]>(
    key,
    () => ApiService.tenants.getTenants(filters),
  )

  // Batch-fetch all contracts (shared cache key — deduplicated across hooks)
  const { data: contractsData } = useSWR<ContractResponse[]>(
    tenantsData && tenantsData.some(t => t.contract_id) ? '/contracts' : null,
    () => ApiService.contracts.getContracts(),
  )

  // Batch-fetch all properties (shared cache key — deduplicated across hooks)
  const { data: propertiesData } = useSWR<PropertyResponse[]>(
    contractsData && contractsData.some(c => c.property_id) ? '/properties' : null,
    () => ApiService.properties.getProperties(),
  )

  // Enrich tenants in-memory using Maps (O(n) instead of O(n*2) API calls)
  const enrichedTenants = useMemo(() => {
    if (!tenantsData) return []

    const contractsMap = new Map<number, ContractResponse>()
    if (contractsData) {
      contractsData.forEach(c => contractsMap.set(c.id, c))
    }

    const propertiesMap = new Map<number, PropertyResponse>()
    if (propertiesData) {
      propertiesData.forEach(p => propertiesMap.set(p.id, p))
    }

    return tenantsData.map((tenant): EnrichedTenant => {
      if (!tenant.contract_id) return { ...tenant, status: 'inativo' }

      const contract = contractsMap.get(tenant.contract_id)
      if (!contract) return { ...tenant, status: 'inativo' }

      const property = contract.property_id ? propertiesMap.get(contract.property_id) : null

      // Calcular dia de vencimento
      const [, , day] = contract.start_date.split('-').map(Number)

      return {
        ...tenant,
        status: contract.status === 'ativo' ? 'ativo' : 'inativo',
        property_name: property?.name,
        property_address: property?.address,
        rent: parseFloat(contract.rent.toString()),
        due_day: day,
        contract_start: contract.start_date,
        contract_end: contract.end_date,
      }
    })
  }, [tenantsData, contractsData, propertiesData])

  const invalidateRelated = async () => {
    await mutateTenants()
    await globalMutate((k: string) => typeof k === 'string' && k.startsWith('/dashboard'), undefined, { revalidate: true })
  }

  const createTenant = async (tenant: any): Promise<TenantResponse | null> => {
    try {
      const newTenant = await ApiService.tenants.createTenant(tenant)
      await invalidateRelated()
      return newTenant
    } catch (err) {
      console.error('❌ Erro ao criar inquilino:', err)
      throw err
    }
  }

  const updateTenant = async (id: number, tenant: any): Promise<TenantResponse | null> => {
    try {
      const updatedTenant = await ApiService.tenants.updateTenant(id, tenant)
      await invalidateRelated()
      return updatedTenant
    } catch (err) {
      console.error('❌ Erro ao atualizar inquilino:', err)
      throw err
    }
  }

  const deleteTenant = async (id: number): Promise<boolean> => {
    try {
      await ApiService.tenants.deleteTenant(id)
      await invalidateRelated()
      return true
    } catch (err) {
      console.error('❌ Erro ao deletar inquilino:', err)
      return false
    }
  }

  return {
    tenants: enrichedTenants,
    loading: tenantsLoading,
    error: tenantsError ? handleApiError(tenantsError) : null,
    refetch: async () => { await mutateTenants() },
    createTenant,
    updateTenant,
    deleteTenant,
  }
}

// Hook para buscar um inquilino específico
export function useTenant(id: number) {
  const { data, error: swrError, isLoading } = useSWR<TenantResponse>(
    id ? `${TENANTS_KEY}/${id}` : null,
    () => ApiService.tenants.getTenant(id),
  )

  return {
    tenant: data ?? null,
    loading: isLoading,
    error: swrError ? handleApiError(swrError) : null,
  }
}