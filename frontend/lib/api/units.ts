import { apiClient, buildQueryString } from './client'
import {
  UnitResponse,
  UnitCreate,
  UnitUpdate,
  UnitFilters,
} from '@/lib/types/api'

export class UnitsService {
  private readonly endpoint = '/units'

  // Listar unidades com filtros
  async getUnits(filters?: UnitFilters): Promise<UnitResponse[]> {
    const queryString = filters ? buildQueryString(filters) : ''
    return apiClient.get<UnitResponse[]>(`${this.endpoint}/${queryString}`)
  }

  // Obter unidade por ID
  async getUnit(id: number): Promise<UnitResponse> {
    return apiClient.get<UnitResponse>(`${this.endpoint}/${id}/`)
  }

  // Criar nova unidade
  async createUnit(unit: UnitCreate): Promise<UnitResponse> {
    return apiClient.post<UnitResponse>(`${this.endpoint}/`, unit)
  }

  // Atualizar unidade
  async updateUnit(id: number, unit: UnitUpdate): Promise<UnitResponse> {
    return apiClient.put<UnitResponse>(`${this.endpoint}/${id}/`, unit)
  }

  // Deletar unidade
  async deleteUnit(id: number): Promise<void> {
    return apiClient.delete<void>(`${this.endpoint}/${id}/`)
  }

  // Obter unidades disponíveis de uma propriedade
  async getAvailableUnits(propertyId: number): Promise<UnitResponse[]> {
    return apiClient.get<UnitResponse[]>(`${this.endpoint}/property/${propertyId}/available/`)
  }
}

// Instância singleton do serviço
export const unitsService = new UnitsService()