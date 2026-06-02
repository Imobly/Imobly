import useSWR, { mutate as globalMutate } from 'swr'
import { ApiService, handleApiError } from '@/lib/api'
import { PropertyResponse, PropertyFilters } from '@/lib/types/api'

// Cache key builder
const PROPERTIES_KEY = '/properties'
const getPropertiesKey = (filters?: PropertyFilters) => {
  const filterStr = filters ? JSON.stringify(filters) : ''
  return filterStr ? `${PROPERTIES_KEY}?${filterStr}` : PROPERTIES_KEY
}

interface UsePropertiesReturn {
  properties: PropertyResponse[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  createProperty: (property: any) => Promise<PropertyResponse | null>
  updateProperty: (id: number, property: any) => Promise<PropertyResponse | null>
  deleteProperty: (id: number) => Promise<boolean>
}

export function useProperties(filters?: PropertyFilters): UsePropertiesReturn {
  const key = getPropertiesKey(filters)

  const { data, error: swrError, isLoading, mutate } = useSWR<PropertyResponse[]>(
    key,
    () => ApiService.properties.getProperties(filters),
  )

  const invalidateRelated = async () => {
    await mutate()
    // Invalidar todas as chaves de properties (include dashboard que depende de properties)
    await globalMutate(
      (k: string) => typeof k === 'string' && (k.startsWith('/dashboard') || k.startsWith('/properties')),
      undefined,
      { revalidate: true }
    )
  }

  const createProperty = async (property: any): Promise<PropertyResponse | null> => {
    try {
      const newProperty = await ApiService.properties.createProperty(property)
      await invalidateRelated()
      return newProperty
    } catch (err) {
      console.error('❌ Erro ao criar propriedade:', err)
      throw err
    }
  }

  const updateProperty = async (id: number, property: any): Promise<PropertyResponse | null> => {
    try {
      const updatedProperty = await ApiService.properties.updateProperty(id, property)
      await invalidateRelated()
      return updatedProperty
    } catch (err) {
      console.error('❌ Erro ao atualizar propriedade:', err)
      throw err
    }
  }

  const deleteProperty = async (id: number): Promise<boolean> => {
    try {
      await ApiService.properties.deleteProperty(id)
      await invalidateRelated()
      return true
    } catch (err) {
      console.error('❌ Erro ao deletar propriedade:', err)
      throw err
    }
  }

  return {
    properties: data ?? [],
    loading: isLoading,
    error: swrError ? handleApiError(swrError) : null,
    refetch: async () => { await mutate() },
    createProperty,
    updateProperty,
    deleteProperty,
  }
}

// Hook para buscar uma propriedade específica
export function useProperty(id: number) {
  const { data, error: swrError, isLoading } = useSWR<PropertyResponse>(
    id ? `${PROPERTIES_KEY}/${id}` : null,
    () => ApiService.properties.getProperty(id),
  )

  return {
    property: data ?? null,
    loading: isLoading,
    error: swrError ? handleApiError(swrError) : null,
  }
}