"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  Home,
  Users,
  DollarSign,
  Wrench,
  TrendingUp,
  TrendingDown,
  Activity,
} from "lucide-react"

interface SystemStatus {
  name: string
  status: "operational" | "warning" | "error" | "maintenance"
  uptime: number
  lastCheck: string
  issues?: string[]
}

interface OperationalMetrics {
  totalProperties: number
  occupiedProperties: number
  activeTenants: number
  activeContracts: number
  overduePayments: number
  urgentMaintenance: number
  monthlyRevenue: number
  monthlyExpenses: number
}

const systemStatuses: SystemStatus[] = [
  {
    name: "Gestão de Imóveis",
    status: "operational",
    uptime: 99.9,
    lastCheck: "2024-01-20T10:30:00",
  },
  {
    name: "Gestão de Inquilinos",
    status: "operational",
    uptime: 99.8,
    lastCheck: "2024-01-20T10:29:00",
  },
  {
    name: "Contratos de Locação",
    status: "warning",
    uptime: 98.5,
    lastCheck: "2024-01-20T10:28:00",
    issues: ["3 contratos vencendo em 15 dias"],
  },
  {
    name: "Sistema de Pagamentos",
    status: "error",
    uptime: 97.2,
    lastCheck: "2024-01-20T10:27:00",
    issues: ["5 pagamentos em atraso", "2 falhas de processamento"],
  },
  {
    name: "Despesas e Manutenção",
    status: "warning",
    uptime: 99.1,
    lastCheck: "2024-01-20T10:26:00",
    issues: ["2 manutenções urgentes pendentes"],
  },
  {
    name: "Sistema de Notificações",
    status: "operational",
    uptime: 99.9,
    lastCheck: "2024-01-20T10:25:00",
  },
]

const operationalMetrics: OperationalMetrics = {
  totalProperties: 12,
  occupiedProperties: 10,
  activeTenants: 10,
  activeContracts: 10,
  overduePayments: 2,
  urgentMaintenance: 1,
  monthlyRevenue: 25000,
  monthlyExpenses: 8500,
}

export function StatusView() {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "operational":
        return <CheckCircle className="h-5 w-5 text-success" />
      case "warning":
        return <AlertTriangle className="h-5 w-5 text-warning" />
      case "error":
        return <XCircle className="h-5 w-5 text-danger" />
      case "maintenance":
        return <Clock className="h-5 w-5 text-blue-500" />
      default:
        return <Activity className="h-5 w-5 text-muted-foreground" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "operational":
        return "Operacional"
      case "warning":
        return "Atenção"
      case "error":
        return "Erro"
      case "maintenance":
        return "Manutenção"
      default:
        return status
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "operational":
        return "bg-success text-success-foreground"
      case "warning":
        return "bg-warning text-warning-foreground"
      case "error":
        return "bg-danger text-danger-foreground"
      case "maintenance":
        return "bg-blue-500 text-white"
      default:
        return "bg-muted text-muted-foreground"
    }
  }

  const occupancyRate = (operationalMetrics.occupiedProperties / operationalMetrics.totalProperties) * 100
  const netIncome = operationalMetrics.monthlyRevenue - operationalMetrics.monthlyExpenses
  const profitMargin = (netIncome / operationalMetrics.monthlyRevenue) * 100

  return (
    <div className="space-y-6">
      {/* Overall System Health */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Status Geral do Sistema
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {systemStatuses.map((system) => (
              <div key={system.name} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">{system.name}</h3>
                  {getStatusIcon(system.status)}
                </div>

                <div className="space-y-2">
                  <Badge className={getStatusColor(system.status)}>{getStatusText(system.status)}</Badge>

                  <div className="text-sm text-muted-foreground">Uptime: {system.uptime}%</div>

                  <Progress value={system.uptime} className="h-2" />

                  <div className="text-xs text-muted-foreground">
                    Última verificação: {new Date(system.lastCheck).toLocaleString("pt-BR")}
                  </div>

                  {system.issues && system.issues.length > 0 && (
                    <div className="mt-2">
                      <div className="text-xs font-medium text-muted-foreground mb-1">Problemas:</div>
                      {system.issues.map((issue, index) => (
                        <div key={index} className="text-xs text-danger">
                          • {issue}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Operational Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Taxa de Ocupação</CardTitle>
            <Home className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{occupancyRate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              {operationalMetrics.occupiedProperties} de {operationalMetrics.totalProperties} imóveis
            </p>
            <Progress value={occupancyRate} className="mt-2 h-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Inquilinos Ativos</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{operationalMetrics.activeTenants}</div>
            <p className="text-xs text-muted-foreground">{operationalMetrics.activeContracts} contratos ativos</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pagamentos Atrasados</CardTitle>
            <AlertTriangle className="h-4 w-4 text-danger" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-danger">{operationalMetrics.overduePayments}</div>
            <p className="text-xs text-muted-foreground">Requer atenção imediata</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Manutenções Urgentes</CardTitle>
            <Wrench className="h-4 w-4 text-warning" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-warning">{operationalMetrics.urgentMaintenance}</div>
            <p className="text-xs text-muted-foreground">Pendentes</p>
          </CardContent>
        </Card>
      </div>

      {/* Financial Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Receita Mensal</CardTitle>
            <TrendingUp className="h-4 w-4 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-success">
              R$ {operationalMetrics.monthlyRevenue.toLocaleString("pt-BR")}
            </div>
            <p className="text-xs text-muted-foreground">Este mês</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Despesas Mensais</CardTitle>
            <TrendingDown className="h-4 w-4 text-danger" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-danger">
              R$ {operationalMetrics.monthlyExpenses.toLocaleString("pt-BR")}
            </div>
            <p className="text-xs text-muted-foreground">Este mês</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Lucro Líquido</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">R$ {netIncome.toLocaleString("pt-BR")}</div>
            <p className="text-xs text-muted-foreground">Margem: {profitMargin.toFixed(1)}%</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Ações Recomendadas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 border rounded-lg">
              <AlertTriangle className="h-5 w-5 text-danger" />
              <div className="flex-1">
                <div className="font-medium">Pagamentos em Atraso</div>
                <div className="text-sm text-muted-foreground">
                  2 inquilinos com pagamentos atrasados precisam ser contatados
                </div>
              </div>
              <Badge className="bg-danger text-danger-foreground">Urgente</Badge>
            </div>

            <div className="flex items-center gap-3 p-3 border rounded-lg">
              <Clock className="h-5 w-5 text-warning" />
              <div className="flex-1">
                <div className="font-medium">Contratos Vencendo</div>
                <div className="text-sm text-muted-foreground">3 contratos vencem nos próximos 15 dias</div>
              </div>
              <Badge className="bg-warning text-warning-foreground">Atenção</Badge>
            </div>

            <div className="flex items-center gap-3 p-3 border rounded-lg">
              <Wrench className="h-5 w-5 text-warning" />
              <div className="flex-1">
                <div className="font-medium">Manutenção Urgente</div>
                <div className="text-sm text-muted-foreground">1 manutenção urgente aguardando agendamento</div>
              </div>
              <Badge className="bg-warning text-warning-foreground">Atenção</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
