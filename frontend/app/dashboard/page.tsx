'use client'

import { useMemo } from 'react'
import { ProtectedRoute } from '../../components/auth/protected-route'
import { DashboardLayout } from '../../components/dashboard-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { currencyFormat } from '@/lib/utils'
import { useRevenueVsExpenses, usePropertiesStatus, useDashboard } from '@/lib/hooks/useDashboard'
import { usePayments } from '@/lib/hooks/usePayments'
import { useExpenses } from '@/lib/hooks/useExpenses'
import { useContracts } from '@/lib/hooks/useContracts'
import { useTenants } from '@/lib/hooks/useTenants'
import { useNotifications } from '@/lib/hooks/useNotifications'
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, PieChart as PieIcon, BarChart as BarIcon, Clock, FileWarning, Info } from 'lucide-react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

const BLUE = '#2563eb' // app primary blue
const RED = '#ef4444'
const PIE_COLORS = [BLUE, RED] // blue for occupied, red for vacant

export default function DashboardPage() {
  // Data hooks
  const { data: revExpData, loading: revExpLoading } = useRevenueVsExpenses(6)
  const { data: propertiesStatus, loading: propertiesLoading } = usePropertiesStatus()
  const { summary } = useDashboard()
  const { payments } = usePayments()
  const { expenses } = useExpenses()
  const { contracts } = useContracts()
  const { tenants } = useTenants()
  const { notifications } = useNotifications()

  // Finance metrics (last 6 months)
  const finance = useMemo(() => {
    const chartRows = revExpData?.data ?? []
    const receitaTotal = chartRows.reduce((s, r) => s + (r.revenue || 0), 0)
    const despesasTotal = chartRows.reduce((s, r) => s + (r.expenses || 0), 0)
    const resultado = receitaTotal - despesasTotal

    const overdueCount = payments.filter(p => p.status === 'overdue').length
    const totalPayments = payments.length || 1
    const inadimplenciaPct = Math.round((overdueCount / totalPayments) * 100)

    return { receitaTotal, despesasTotal, resultado, overdueCount, inadimplenciaPct, chartRows }
  }, [revExpData, payments])

  // Occupancy metrics
  const occupancy = useMemo(() => {
    const props = propertiesStatus?.properties ?? []
    const total = props.length
    const occupied = props.filter(p => p.status === 'occupied').length
    const vacant = props.filter(p => p.status === 'vacant').length
    const rate = total > 0 ? Math.round((occupied / total) * 100) : Math.round((summary?.properties.occupancy_rate ?? 0) * 100)
    return { total, occupied, vacant, rate, pieData: [ { name: 'Ocupados', value: occupied }, { name: 'Vagos', value: vacant } ] }
  }, [propertiesStatus, summary])

  // Contracts & tenants
  const contractsTenants = useMemo(() => {
    const activeContracts = contracts.filter(c => c.status === 'active')
    const activeTenants = tenants.filter(t => t.status === 'active')
    const now = new Date()
    const in30 = new Date(); in30.setDate(now.getDate() + 30)
    const last30 = new Date(); last30.setDate(now.getDate() - 30)

    const expiringSoon = contracts.filter(c => {
      const end = new Date(c.end_date)
      return end >= now && end <= in30 && c.status === 'active'
    }).slice(0, 6)

    const recentlyEnded = contracts.filter(c => {
      const end = new Date(c.end_date)
      return end < now && end >= last30 && (c.status === 'expired' || c.status === 'terminated')
    }).slice(0, 6)

    return { activeContracts, activeTenants, expiringSoon, recentlyEnded }
  }, [contracts, tenants])

  // Insights
  const insights = useMemo(() => {
    const rows = finance.chartRows
    if (!rows || rows.length < 2) return []
    const last = rows[rows.length - 1]
    const prev = rows[rows.length - 2]
    const lastProfit = (last.revenue || 0) - (last.expenses || 0)
    const prevProfit = (prev.revenue || 0) - (prev.expenses || 0)
    const diffPct = prevProfit === 0 ? 0 : Math.round(((lastProfit - prevProfit) / Math.max(Math.abs(prevProfit), 1)) * 100)

    const expiringCount = contractsTenants.expiringSoon.length
    const longVacancy = occupancy.vacant > 0 && occupancy.rate < 70

    const msgs: Array<{ icon: React.ReactNode, text: string }> = []
    msgs.push({ icon: diffPct >= 0 ? <TrendingUp className="h-4 w-4 text-green-600"/> : <TrendingDown className="h-4 w-4 text-red-600"/>, text: `Seu lucro ${diffPct >= 0 ? 'aumentou' : 'caiu'} ${Math.abs(diffPct)}% em relação ao mês anterior` })
    msgs.push({ icon: <Clock className="h-4 w-4 text-yellow-600"/>, text: `${expiringCount} contratos vencem nos próximos 30 dias` })
    if (longVacancy) msgs.push({ icon: <AlertTriangle className="h-4 w-4 text-red-600"/>, text: `Há imóveis vagos afetando a taxa de ocupação (${occupancy.rate}%)` })
    return msgs
  }, [finance.chartRows, contractsTenants.expiringSoon, occupancy.rate, occupancy.vacant])

  return (
    <ProtectedRoute>
      <DashboardLayout>
      <div className="container mx-auto px-4 py-6 space-y-10">
        {/* Título */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
            <p className="text-muted-foreground">Visão financeira e operacional</p>
          </div>
        </div>

        {/* BLOCO 1 — Visão Financeira */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <BarIcon className="h-5 w-5 text-blue-600" />
            <h2 className="text-xl font-semibold">Visão Financeira</h2>
          </div>

          {/* Indicadores */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">Receita total (6 meses)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">{currencyFormat(finance.receitaTotal)}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">Despesas totais (6 meses)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">{currencyFormat(finance.despesasTotal)}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">Resultado</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${finance.resultado >= 0 ? 'text-blue-600' : 'text-red-600'}`}>{currencyFormat(finance.resultado)}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">Inadimplência atual</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  <span className="text-red-600">{finance.overdueCount}</span>
                  <span className="text-muted-foreground ml-2 text-sm">({finance.inadimplenciaPct}%)</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Gráfico Receita x Despesas (últimos 6 meses) */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Receita x Despesas (últimos 6 meses)</CardTitle>
            </CardHeader>
            <CardContent className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={finance.chartRows}>
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="revenue" name="Receita" fill={BLUE} />
                  <Bar dataKey="expenses" name="Despesas" fill="#ef4444" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </section>

        <Separator />

        {/* BLOCO 2 — Ocupação de Imóveis */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <PieIcon className="h-5 w-5 text-blue-600" />
            <h2 className="text-xl font-semibold">Ocupação de Imóveis</h2>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardContent className="h-72 pt-6">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={occupancy.pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={100}>
                      {occupancy.pieData.map((entry, idx) => (
                        <Cell key={`cell-${idx}`} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Legend />
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <div className="grid gap-4">
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Taxa de Ocupação</CardTitle></CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{occupancy.rate}%</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Totais</CardTitle></CardHeader>
                <CardContent>
                  <div className="text-sm text-muted-foreground">Imóveis: <span className="font-semibold text-foreground">{occupancy.total}</span></div>
                  <div className="text-sm text-muted-foreground">Ocupados: <span className="font-semibold text-blue-600">{occupancy.occupied}</span></div>
                  <div className="text-sm text-muted-foreground">Vagos: <span className="font-semibold text-red-600">{occupancy.vacant}</span></div>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        <Separator />

        {/* BLOCO 3 — Contratos & Inquilinos */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-xl font-semibold">Contratos e Inquilinos</h2>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Contratos ativos</CardTitle></CardHeader>
              <CardContent><div className="text-2xl font-bold text-green-600">{contractsTenants.activeContracts.length}</div></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Inquilinos ativos</CardTitle></CardHeader>
              <CardContent><div className="text-2xl font-bold">{contractsTenants.activeTenants.length}</div></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Vencem em 30 dias</CardTitle></CardHeader>
              <CardContent><div className="text-2xl font-bold text-yellow-600">{contractsTenants.expiringSoon.length}</div></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Encerrados (30 dias)</CardTitle></CardHeader>
              <CardContent><div className="text-2xl font-bold text-muted-foreground">{contractsTenants.recentlyEnded.length}</div></CardContent>
            </Card>
          </div>

          <div className="grid gap-6 md:grid-cols-2 mt-6">
            <Card>
              <CardHeader><CardTitle>Próximos a vencer</CardTitle></CardHeader>
              <CardContent>
                {contractsTenants.expiringSoon.length === 0 ? (
                  <p className="text-muted-foreground">Nenhum contrato próximo do vencimento.</p>
                ) : (
                  <ul className="space-y-2">
                    {contractsTenants.expiringSoon.map(c => (
                      <li key={c.id} className="flex items-center justify-between text-sm">
                        <span>Contrato #{c.id} • Imóvel #{c.property_id} • Inquilino #{c.tenant_id}</span>
                        <Badge variant="outline"><Clock className="h-3 w-3 mr-1"/> {new Date(c.end_date).toLocaleDateString()}</Badge>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Encerrados recentemente</CardTitle></CardHeader>
              <CardContent>
                {contractsTenants.recentlyEnded.length === 0 ? (
                  <p className="text-muted-foreground">Nenhum contrato encerrado nos últimos 30 dias.</p>
                ) : (
                  <ul className="space-y-2">
                    {contractsTenants.recentlyEnded.map(c => (
                      <li key={c.id} className="flex items-center justify-between text-sm">
                        <span>Contrato #{c.id} • Imóvel #{c.property_id} • Inquilino #{c.tenant_id}</span>
                        <Badge variant="secondary">{new Date(c.end_date).toLocaleDateString()}</Badge>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>
        </section>

        <Separator />

        {/* BLOCO 4 — Alertas & Ações Pendentes */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <h2 className="text-xl font-semibold">Alertas e Ações Pendentes</h2>
          </div>
          <Card>
            <CardContent className="pt-6">
              {notifications.length === 0 ? (
                <p className="text-muted-foreground">Nenhum alerta no momento.</p>
              ) : (
                <ul className="space-y-3">
                  {notifications.map(n => (
                    <li key={n.id} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        {n.type === 'payment_overdue' ? <AlertTriangle className="h-4 w-4 text-red-600"/> : n.type === 'contract_expiring' ? <Clock className="h-4 w-4 text-yellow-600"/> : <Info className="h-4 w-4 text-blue-600"/>}
                        <span className="font-medium">{n.title}</span>
                        <span className="text-muted-foreground">{n.message}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={n.priority === 'urgent' ? 'destructive' : n.priority === 'high' ? 'secondary' : 'outline'}>{n.priority}</Badge>
                        <Badge variant={n.read_status ? 'outline' : 'secondary'}>{n.read_status ? 'lida' : 'não lida'}</Badge>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </section>

        {/* 🧠 Extra — Insights */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-xl font-semibold">Insights</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {insights.length === 0 ? (
              <Card><CardContent className="pt-6"><p className="text-muted-foreground">Sem insights suficientes ainda.</p></CardContent></Card>
            ) : insights.map((i, idx) => (
              <Card key={idx}>
                <CardContent className="pt-6 flex items-center gap-3">
                  {i.icon}
                  <span className="text-sm">{i.text}</span>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}