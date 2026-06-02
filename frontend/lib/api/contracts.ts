import { apiClient, buildQueryString } from './client'
import {
  ContractResponse,
  ContractCreate,
  ContractUpdate,
  ContractFilters,
} from '@/lib/types/api'

export class ContractsService {
  private readonly endpoint = '/contracts'

  // Listar contratos com filtros
  async getContracts(filters?: ContractFilters): Promise<ContractResponse[]> {
    const queryString = filters ? buildQueryString(filters) : ''
    return apiClient.get<ContractResponse[]>(`${this.endpoint}/${queryString}`)
  }

  // Obter contrato por ID
  async getContract(id: number): Promise<ContractResponse> {
    return apiClient.get<ContractResponse>(`${this.endpoint}/${id}`)
  }

  // Criar novo contrato
  async createContract(contract: ContractCreate): Promise<ContractResponse> {
    return apiClient.post<ContractResponse>(`${this.endpoint}/`, contract)
  }

  // Atualizar contrato
  async updateContract(id: number, contract: ContractUpdate): Promise<ContractResponse> {
    return apiClient.put<ContractResponse>(`${this.endpoint}/${id}`, contract)
  }

  // Renovar contrato
  async renewContract(
    id: number,
    newEndDate: string,
    newRent?: number
  ): Promise<ContractResponse> {
    const params: any = { new_end_date: newEndDate }
    if (newRent !== undefined) {
      params.new_rent = newRent
    }
    return apiClient.patch<ContractResponse>(`${this.endpoint}/${id}/renew`, null, { params })
  }

  // Atualizar status do contrato
  async updateStatus(
    id: number,
    newStatus: 'ativo' | 'inativo' | 'expirado'
  ): Promise<ContractResponse> {
    return apiClient.patch<ContractResponse>(`${this.endpoint}/${id}/status`, null, {
      params: { new_status: newStatus }
    })
  }

  // Obter contratos que vencem em X dias
  async getExpiringContracts(daysAhead: number = 30): Promise<ContractResponse[]> {
    return apiClient.get<ContractResponse[]>(`${this.endpoint}/expiring`, {
      params: { days_ahead: daysAhead }
    })
  }

  // Obter contratos ativos
  async getActiveContracts(): Promise<ContractResponse[]> {
    return apiClient.get<ContractResponse[]>(`${this.endpoint}/active`)
  }

  // Deletar contrato
  async deleteContract(id: number): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`${this.endpoint}/${id}`)
  }
}

// Instância singleton do serviço
export const contractsService = new ContractsService()