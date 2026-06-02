import useSWR from 'swr'
import { dashboardService } from '@/lib/api/dashboard'
import {
  DashboardSummary,
  DashboardStats,
  RevenueVsExpensesData,
  PropertiesStatusResponse,
} from '@/lib/types/api'

// Cache keys
const DASHBOARD_STATS_KEY = '/dashboard/stats'
const DASHBOARD_REVENUE_KEY = '/dashboard/revenue'
const DASHBOARD_PROPERTIES_KEY = '/dashboard/properties-status'

interface UseDashboardReturn {
  summary: DashboardSummary | null
  stats: DashboardStats | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useDashboard(period?: string): UseDashboardReturn {
  const { data: statsData, error: swrError, isLoading, mutate } = useSWR<DashboardStats>(
    period ? `${DASHBOARD_STATS_KEY}?period=${period}` : DASHBOARD_STATS_KEY,
    () => dashboardService.getStats(),
  )

  // Mapear resposta do /stats para o formato DashboardSummary esperado pelo componente
  const summary: DashboardSummary | null = statsData ? {
    properties: {
      total: statsData?.properties?.total || 0,
      occupied_units: statsData?.properties?.occupied || 0,
      vacant_units: statsData?.properties?.vacant || 0,
      occupancy_rate: statsData?.properties?.occupancy_rate || 0
    },
    contracts: {
      active: 0,
      expiring_soon: 0,
      expired: 0
    },
    financial: {
      monthly_revenue: statsData?.financial?.monthly_income || 0,
      monthly_expenses: statsData?.financial?.monthly_expenses || 0,
      overdue_payments: statsData?.financial?.overdue_payments || 0,
      total_received: statsData?.financial?.monthly_income || 0
    }
  } : null

  return {
    summary,
    stats: statsData ?? null,
    loading: isLoading,
    error: swrError ? (swrError?.detail || 'Erro ao carregar dashboard') : null,
    refetch: async () => { await mutate() },
  }
}

// Hook para dados de receitas vs despesas
export function useRevenueVsExpenses(months: number = 6) {
  const { data, error: swrError, isLoading } = useSWR<RevenueVsExpensesData>(
    `${DASHBOARD_REVENUE_KEY}?months=${months}`,
    async () => {
      const chartData = await dashboardService.getRevenueVsExpenses(months)
      // Validar dados do gráfico
      if (chartData && chartData.data) {
        return {
          ...chartData,
          data: chartData.data.map(item => ({
            month: item.month || '',
            revenue: item.revenue || 0,
            expenses: item.expenses || 0,
            profit: item.profit || 0
          }))
        }
      }
      return { data: [] }
    },
  )

  return {
    data: data ?? null,
    loading: isLoading,
    error: swrError ? (swrError?.detail || 'Erro ao carregar gráfico') : null,
  }
}

// Hook para status das propriedades
export function usePropertiesStatus(period?: string) {
  const { data, error: swrError, isLoading } = useSWR<PropertiesStatusResponse>(
    period ? `${DASHBOARD_PROPERTIES_KEY}?period=${period}` : DASHBOARD_PROPERTIES_KEY,
    async () => {
      const propertiesData = await dashboardService.getPropertiesStatus()
      if (propertiesData) {
        return {
          summary: propertiesData.summary ? {
            occupancy_rate: propertiesData.summary.occupancy_rate || 0,
            total_revenue: propertiesData.summary.total_revenue || 0,
            total_expenses: propertiesData.summary.total_expenses || 0
          } : undefined,
          properties: (propertiesData.properties || []).map((prop: any) => ({
            id: prop.id || prop.property_id || 0,
            property_id: prop.id || prop.property_id || 0,
            property_name: prop.name || prop.property_name || 'Imóvel sem nome',
            name: prop.name || prop.property_name,
            address: prop.address,
            status: prop.status || 'vacant',
            type: prop.type,
            tenant_id: prop.tenant_id ?? null,
            active_contracts: prop.active_contracts ?? 0,
            expected_monthly_revenue: prop.expected_monthly_revenue ?? 0,
            received_monthly_revenue: prop.received_monthly_revenue ?? 0,
            monthly_revenue: prop.monthly_revenue ?? 0,
            monthly_expenses: prop.monthly_expenses ?? 0,
            net_profit: prop.net_profit ?? 0,
            occupancy_rate: prop.occupancy_rate ?? 0,
            bedrooms: prop.bedrooms ?? 0,
            bathrooms: prop.bathrooms ?? 0,
            parking_spaces: prop.parking_spaces ?? 0
          }))
        }
      }
      return { properties: [] }
    },
  )

  return {
    data: data ?? null,
    loading: isLoading,
    error: swrError ? (swrError?.detail || 'Erro ao carregar propriedades') : null,
  }
}