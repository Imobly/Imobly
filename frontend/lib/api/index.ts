// Cliente HTTP base
export { apiClient, handleApiError, buildQueryString } from './client'

// Serviços da API
export { propertiesService } from './properties'
export { tenantsService } from './tenants'
export { paymentsService } from './payments'
export { expensesService } from './expenses'
export { notificationsService } from './notifications'
export { contractsService } from './contracts'
export { unitsService } from './units'
export { dashboardService, generalService } from './dashboard'

// Importações para a classe principal
import { propertiesService } from './properties'
import { tenantsService } from './tenants'
import { paymentsService } from './payments'
import { expensesService } from './expenses'
import { notificationsService } from './notifications'
import { contractsService } from './contracts'
import { unitsService } from './units'
import { dashboardService, generalService } from './dashboard'

// Tipos da API
export * from '@/lib/types/api'

// Classe principal para acesso a todos os serviços
export class ApiService {
  static properties = propertiesService
  static tenants = tenantsService
  static payments = paymentsService
  static expenses = expensesService
  static notifications = notificationsService
  static contracts = contractsService
  static units = unitsService
  static dashboard = dashboardService
  static general = generalService
  
  // Método para testar conectividade
  static async testConnection(): Promise<boolean> {
    try {
      await generalService.getRoot()
      return true
    } catch (error) {
      console.error('Falha na conexão com a API:', error)
      return false
    }
  }
  
  // Método para obter informações da API
  static async getApiInfo(): Promise<any> {
    try {
      return await generalService.getRoot()
    } catch (error) {
      console.error('Falha ao obter informações da API:', error)
      return null
    }
  }
}

export default ApiService