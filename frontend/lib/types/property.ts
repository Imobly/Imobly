// Import tipos da API para compatibilidade
import { PropertyResponse, UnitResponse } from './api'
import { toNumber } from '@/lib/utils/format'

export interface Unit {
  id: number
  number: string
  area: number
  bedrooms: number
  bathrooms: number
  rent: number
  status: 'vacant' | 'occupied' | 'maintenance'
  tenant?: string
  property_id?: number
  created_at?: string
  updated_at?: string
}

/**
 * Propriedade ainda não persistida: `id` só existe depois de salva.
 * Usado pelo formulário, que serve tanto para criação quanto edição.
 */
export type PropertyDraft = Omit<Property, 'id'> & { id?: number }

export interface Property {
  id: number
  name: string
  address: string
  neighborhood: string
  city: string
  state: string
  zipCode: string
  zip_code?: string // compatibilidade com API
  type: 'apartment' | 'house' | 'commercial' | 'studio'
  area: number
  bedrooms: number
  bathrooms: number
  parkingSpaces: number
  parking_spaces?: number // compatibilidade com API
  rent: number
  status: 'vacant' | 'occupied' | 'maintenance' | 'inactive'
  description?: string
  images?: string[]
  units?: Unit[]
  isResidential?: boolean
  is_residential?: boolean // compatibilidade com API
  tenant_id?: number | null
  createdAt?: string
  created_at?: string // compatibilidade com API
  updated_at?: string
  pendingFiles?: File[] // Arquivos pendentes para upload após criar propriedade
}

export interface PropertyFormData {
  id?: number
  name: string
  address: string
  neighborhood: string
  city: string
  state: string
  zipCode: string
  zip_code?: string
  type: 'apartment' | 'house' | 'commercial' | 'studio'
  area: number
  bedrooms: number
  bathrooms: number
  parkingSpaces: number
  parking_spaces?: number
  rent: number
  status: 'vacant' | 'occupied' | 'maintenance' | 'inactive'
  description?: string
  images?: string[]
  units?: Unit[]
  isResidential?: boolean
  is_residential?: boolean
  tenant_id?: number | null
  createdAt?: string
  created_at?: string
  updated_at?: string
}

// Funções utilitárias para conversão entre formatos
export const convertApiToProperty = (apiProperty: PropertyResponse): Property => ({
  id: apiProperty.id,
  name: apiProperty.name,
  address: apiProperty.address,
  neighborhood: apiProperty.neighborhood,
  city: apiProperty.city,
  state: apiProperty.state,
  zipCode: apiProperty.zip_code,
  zip_code: apiProperty.zip_code,
  type: apiProperty.type,
  // `Decimal` do Pydantic chega no JSON como STRING ("600.0"), não como
  // número. Sem esta coerção, `rent.toLocaleString()` devolvia a string crua
  // ("600.0" na listagem) e a máscara do formulário lia os dígitos como
  // centavos (R$ 60,00 na edição) — dois números diferentes para o mesmo
  // aluguel.
  area: toNumber(apiProperty.area),
  bedrooms: toNumber(apiProperty.bedrooms),
  bathrooms: toNumber(apiProperty.bathrooms),
  parkingSpaces: toNumber(apiProperty.parking_spaces),
  parking_spaces: toNumber(apiProperty.parking_spaces),
  rent: toNumber(apiProperty.rent),
  status: apiProperty.status,
  description: apiProperty.description,
  images: apiProperty.images,
  isResidential: apiProperty.is_residential,
  is_residential: apiProperty.is_residential,
  tenant_id: apiProperty.tenant_id ?? null,
  createdAt: apiProperty.created_at,
  created_at: apiProperty.created_at,
  updated_at: apiProperty.updated_at
})

export const convertPropertyToApi = (property: PropertyFormData): Partial<PropertyResponse> => {
  // A API só aceita número canônico. `toNumber` cobre tanto o que o
  // formulário produz (texto no separador da máquina, "85,5") quanto o que
  // veio da própria API (decimal canônico, "85.5") — `parseFloat` truncava o
  // primeiro caso em 85.
  const area = toNumber(property.area)
  const bedrooms = Math.trunc(toNumber(property.bedrooms))
  const bathrooms = Math.trunc(toNumber(property.bathrooms))
  const parkingSpaces = Math.trunc(toNumber(property.parkingSpaces ?? property.parking_spaces ?? 0))
  const rent = toNumber(property.rent)
  
  const apiData = {
    name: property.name,
    address: property.address,
    neighborhood: property.neighborhood,
    city: property.city,
    state: property.state,
    zip_code: property.zipCode || property.zip_code,
    type: property.type,
    area: area,
    bedrooms: bedrooms,
    bathrooms: bathrooms,
    parking_spaces: parkingSpaces,
    rent: rent,
    status: property.status,
    description: property.description,
    images: property.images,
    is_residential: property.isResidential ?? property.is_residential ?? false,
    tenant_id: property.tenant_id ?? null
  }

  return apiData
}