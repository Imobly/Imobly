// Import tipos da API para compatibilidade
import { PropertyResponse, UnitResponse } from './api'

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
  area: apiProperty.area,
  bedrooms: apiProperty.bedrooms,
  bathrooms: apiProperty.bathrooms,
  parkingSpaces: apiProperty.parking_spaces,
  parking_spaces: apiProperty.parking_spaces,
  rent: apiProperty.rent,
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
  // Garantir que valores numéricos estejam no formato correto
  const area = typeof property.area === 'string' ? parseFloat(property.area) : property.area
  const bedrooms = typeof property.bedrooms === 'string' ? parseInt(property.bedrooms) : property.bedrooms
  const bathrooms = typeof property.bathrooms === 'string' ? parseInt(property.bathrooms) : property.bathrooms
  const parkingSpaces = typeof property.parkingSpaces === 'string' ? parseInt(property.parkingSpaces) : (property.parkingSpaces || property.parking_spaces || 0)
  const rent = typeof property.rent === 'string' ? parseFloat(property.rent) : property.rent
  
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