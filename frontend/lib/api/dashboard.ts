import { apiClient } from './client'
import {
  DashboardSummary,
  DashboardStats,
  DashboardSummaryResponse,
  RevenueVsExpensesData,
  PropertiesStatusResponse,
  RootResponse,
} from '@/lib/types/api'

export class DashboardService {
  private readonly endpoint = '/dashboard'

  // Obter estatísticas básicas
  async getStats(): Promise<DashboardStats> {
    return apiClient.get<DashboardStats>(`${this.endpoint}/stats`)
  }

  // Obter resumo consolidado (endpoint /summary)
  async getSummary(): Promise<DashboardSummaryResponse> {
    return apiClient.get<DashboardSummaryResponse>(`${this.endpoint}/summary`)
  }

  // Obter dados de receitas vs despesas
  // Mapeia para /revenue/trend (o endpoint /revenue-vs-expenses não existe no backend)
  async getRevenueVsExpenses(months: number = 12, propertyId?: number): Promise<RevenueVsExpensesData> {
    const params = new URLSearchParams({ months: months.toString() })
    if (propertyId) params.append('property_id', propertyId.toString())
    const response = await apiClient.get<{ trend: any[]; period_months: number }>(
      `${this.endpoint}/revenue/trend?${params}`
    )
    // Backend retorna { trend: [{month, year, revenue, expenses, profit}] }
    // Frontend espera { data: [{month, revenue, expenses, profit}] }
    return { data: response?.trend ?? [] }
  }

  // Obter status das propriedades
  async getPropertiesStatus(): Promise<PropertiesStatusResponse> {
    const properties = await apiClient.get<any[]>('/properties/')
    return { properties: properties ?? [] }
  }

  // Obter overview completo do dashboard
  async getOverview(): Promise<any> {
    return apiClient.get(`${this.endpoint}/overview`)
  }
}

export class GeneralService {
  // Root endpoint (health check)
  async getRoot(): Promise<RootResponse> {
    return apiClient.get<RootResponse>('/')
  }
}

// Instâncias singleton dos serviços
export const dashboardService = new DashboardService()
export const generalService = new GeneralService()