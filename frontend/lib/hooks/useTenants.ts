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

  /**
   * Revalida em SEGUNDO PLANO os caches que derivam de inquilinos.
   *
   * Deliberadamente sem `await`: antes, `invalidateRelated` era aguardado
   * dentro de cada mutação, então salvar um inquilino só retornava depois de
   * um GET /tenants completo + a revalidação do dashboard. Com o banco em
   * us-west-2, isso somava round-trips que o usuário esperava olhando spinner.
   * O cache da lista já foi atualizado com a resposta real da API — estas
   * revalidações só existem para campos derivados (status vindo do contrato,
   * agregados do dashboard) e podem chegar alguns instantes depois.
   */
  const revalidarDerivados = () => {
    globalMutate(
      (k: string) => typeof k === 'string' && (k.startsWith('/dashboard') || k === '/contracts'),
      undefined,
      { revalidate: true },
    ).catch(() => {
      // Revalidação de segundo plano: uma falha aqui não deve virar
      // unhandled rejection nem incomodar o usuário — a mutação principal
      // já foi confirmada pela API. O SWR tentará de novo no próximo acesso.
    })
  }

  const createTenant = async (tenant: any): Promise<TenantResponse | null> => {
    // Registro provisório mostrado na hora. O id negativo nunca colide com um
    // id real do Postgres (sempre positivo), então se algo der errado no meio
    // do caminho a entrada fantasma é identificável.
    const otimista = {
      ...tenant,
      id: -Date.now(),
      status: 'inativo',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    } as TenantResponse

    let criado: TenantResponse | null = null
    try {
      await mutateTenants(
        async (atual) => {
          criado = await ApiService.tenants.createTenant(tenant)
          // Troca o provisório pelo registro real devolvido pela API.
          return [...(atual ?? []), criado]
        },
        {
          optimisticData: (atual) => [...(atual ?? []), otimista],
          // Se o POST falhar, o SWR restaura sozinho a lista anterior.
          rollbackOnError: true,
          // A resposta da API já é a verdade — não precisamos de um GET extra.
          populateCache: true,
          revalidate: false,
        },
      )
      revalidarDerivados()
      return criado
    } catch (err) {
      console.error('Erro ao criar inquilino:', err)
      throw err
    }
  }

  const updateTenant = async (id: number, tenant: any): Promise<TenantResponse | null> => {
    let atualizado: TenantResponse | null = null
    try {
      await mutateTenants(
        async (atual) => {
          atualizado = await ApiService.tenants.updateTenant(id, tenant)
          return (atual ?? []).map(t => (t.id === id ? atualizado! : t))
        },
        {
          // Mescla os campos enviados sobre o registro em cache: a UI reflete
          // a edição imediatamente, sem esperar o round-trip.
          optimisticData: (atual) =>
            (atual ?? []).map(t => (t.id === id ? { ...t, ...tenant } : t)),
          rollbackOnError: true,
          populateCache: true,
          revalidate: false,
        },
      )
      revalidarDerivados()
      return atualizado
    } catch (err) {
      console.error('Erro ao atualizar inquilino:', err)
      throw err
    }
  }

  const deleteTenant = async (id: number): Promise<boolean> => {
    try {
      await mutateTenants(
        async (atual) => {
          await ApiService.tenants.deleteTenant(id)
          return (atual ?? []).filter(t => t.id !== id)
        },
        {
          optimisticData: (atual) => (atual ?? []).filter(t => t.id !== id),
          rollbackOnError: true,
          populateCache: true,
          revalidate: false,
        },
      )
      revalidarDerivados()
      return true
    } catch (err) {
      // Propaga em vez de devolver `false`. Devolvendo false, quem chamava não
      // entrava no `catch` e exibia "deletado com sucesso" mesmo quando o
      // backend recusava a exclusão (ex.: inquilino com contrato vinculado) —
      // e agora, com a linha reaparecendo pelo rollback, a mensagem errada
      // ficaria ainda mais confusa.
      console.error('Erro ao deletar inquilino:', err)
      throw err
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