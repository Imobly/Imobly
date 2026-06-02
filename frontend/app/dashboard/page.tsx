'use client'

import { useState, useMemo } from 'react'
import { ProtectedRoute } from '../../components/auth/protected-route'
import { DashboardLayout } from '../../components/dashboard-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { currencyFormat } from '@/lib/utils'
import { usePropertiesStatus } from '@/lib/hooks/useDashboard'
import { usePayments } from '@/lib/hooks/usePayments'
import { useExpenses } from '@/lib/hooks/useExpenses'
import { useContracts } from '@/lib/hooks/useContracts'
import { useTenants } from '@/lib/hooks/useTenants'
import { contractsService } from '@/lib/api/contracts'
import { PieChart as PieIcon, BarChart as BarIcon, Clock, AlertTriangle, XCircle } from 'lucide-react'
import { toast } from 'sonner'
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

const BLUE = '#2563eb'
const RED = '#ef4444'
const GREEN = '#22c55e'
const AMBER = '#f59e0b'
const PIE_COLORS = [BLUE, RED, AMBER] // occupied, vacant, maintenance

const MONTH_NAMES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

const TYPE_LABELS: Record<string, string> = {
  apartment: 'Apartamentos',
  house: 'Casas',
  commercial: 'Salas Comerciais',
  studio: 'Studios',
}
const TYPE_COLORS: Record<string, string> = {
  apartment: BLUE,
  house: GREEN,
  commercial: AMBER,
  studio: '#8b5cf6',
}

// Palette for expense category donut chart
const DONUT_COLORS = ['#2563eb', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316']

export default function DashboardPage() {
  // Data hooks
  const { data: propertiesStatus } = usePropertiesStatus()
  const { payments } = usePayments()
  const { expenses } = useExpenses()
  const { contracts, refetch: refetchContracts } = useContracts()
  const { tenants, refetch: refetchTenants } = useTenants()

  // ── Filter state (global) ──
  const now = new Date()
  const [filterYear, setFilterYear] = useState<string>(String(now.getFullYear()))
  const [filterMonth, setFilterMonth] = useState<string>('all')
  const [filterProperty, setFilterProperty] = useState<string>('all')
  const [filterCategory, setFilterCategory] = useState<string>('all')

  // Available years (from payments/expenses, or just current)
  const availableYears = useMemo(() => {
    const years = new Set<number>()
    payments.forEach(p => { if (p.due_date) years.add(new Date(p.due_date).getFullYear()) })
    expenses.forEach(e => { if (e.date) years.add(new Date(e.date).getFullYear()) })
    years.add(now.getFullYear())
    return Array.from(years).sort((a, b) => b - a)
  }, [payments, expenses])

  // Property list for filter dropdown
  const propertyList = useMemo(() => {
    return (propertiesStatus?.properties ?? []).map(p => ({
      id: p.id || p.property_id || 0,
      name: p.property_name || p.name || `Imóvel #${p.id}`,
    }))
  }, [propertiesStatus])

  // Expense category list for filter dropdown
  const expenseCategories = useMemo(() => {
    const cats = new Set<string>()
    expenses.forEach(e => { if (e.category) cats.add(e.category) })
    return Array.from(cats).sort()
  }, [expenses])

  // ── Financial metrics with filters ──
  const finance = useMemo(() => {
    const year = parseInt(filterYear)

    // Filter payments → revenue (paid + partial)
    const filteredPayments = payments.filter(p => {
      if (p.status !== 'pago' && p.status !== 'parcial') return false
      const pDate = p.payment_date ? new Date(p.payment_date) : (p.due_date ? new Date(p.due_date) : null)
      if (!pDate) return false
      if (pDate.getFullYear() !== year) return false
      if (filterMonth !== 'all' && pDate.getMonth() + 1 !== parseInt(filterMonth)) return false
      if (filterProperty !== 'all' && String(p.property_id) !== filterProperty) return false
      return true
    })

    // Filter expenses
    const filteredExpenses = expenses.filter(e => {
      const eDate = e.date ? new Date(e.date) : null
      if (!eDate) return false
      if (eDate.getFullYear() !== year) return false
      if (filterMonth !== 'all' && eDate.getMonth() + 1 !== parseInt(filterMonth)) return false
      if (filterProperty !== 'all' && String(e.property_id) !== filterProperty) return false
      if (filterCategory !== 'all' && e.category !== filterCategory) return false
      return true
    })

    const receitaTotal = filteredPayments.reduce((sum, p) => sum + (p.total_amount || p.amount || 0), 0)
    const despesasTotal = filteredExpenses.reduce((sum, e) => sum + (Number(e.amount) || 0), 0)
    const resultado = receitaTotal - despesasTotal

    return { receitaTotal, despesasTotal, resultado, filteredPayments, filteredExpenses }
  }, [payments, expenses, filterYear, filterMonth, filterProperty, filterCategory])

  // ── Despesas donut chart data (grouped by category) ──
  const expensesByCategory = useMemo(() => {
    const catMap = new Map<string, number>()
    finance.filteredExpenses.forEach(e => {
      const cat = e.category || 'Outros'
      catMap.set(cat, (catMap.get(cat) || 0) + (Number(e.amount) || 0))
    })
    return Array.from(catMap.entries())
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
  }, [finance.filteredExpenses])

  // ── Ganhos por Imóvel horizontal bar data ──
  const revenueByProperty = useMemo(() => {
    const propMap = new Map<number, number>()
    finance.filteredPayments.forEach(p => {
      propMap.set(p.property_id, (propMap.get(p.property_id) || 0) + (p.total_amount || p.amount || 0))
    })
    const props = propertiesStatus?.properties ?? []
    return Array.from(propMap.entries())
      .map(([propId, value]) => {
        const prop = props.find(pr => (pr.id || pr.property_id) === propId)
        return { name: prop?.property_name || prop?.name || `Imóvel #${propId}`, value }
      })
      .sort((a, b) => b.value - a.value)
  }, [finance.filteredPayments, propertiesStatus])

  // ── Occupancy metrics ──
  const occupancy = useMemo(() => {
    const props = propertiesStatus?.properties ?? []
    const total = props.length
    const occupied = props.filter(p => p.status === 'occupied' || p.tenant_id).length
    const vacant = props.filter(p => p.status === 'vacant' && !p.tenant_id).length
    const maintenance = props.filter(p => p.status === 'maintenance').length
    const rate = total > 0 ? Math.round((occupied / total) * 100) : 0
    const pieData = [
      { name: 'Ocupados', value: occupied },
      { name: 'Vagos', value: vacant },
      ...(maintenance > 0 ? [{ name: 'Manutenção', value: maintenance }] : []),
    ]
    return { total, occupied, vacant, maintenance, rate, pieData }
  }, [propertiesStatus])

  // ── Property type distribution ──
  const typeDistribution = useMemo(() => {
    const props = propertiesStatus?.properties ?? []
    const countMap = new Map<string, number>()
    props.forEach(p => {
      const t = p.type || 'other'
      countMap.set(t, (countMap.get(t) || 0) + 1)
    })
    return Array.from(countMap.entries())
      .map(([type, count]) => ({
        name: TYPE_LABELS[type] || type,
        value: count,
        fill: TYPE_COLORS[type] || '#94a3b8',
      }))
      .sort((a, b) => b.value - a.value)
  }, [propertiesStatus])

  // ── Contracts & tenants ──
  const contractsTenants = useMemo(() => {
    const activeContracts = contracts.filter(c => c.status === 'ativo')
    const nowDate = new Date()
    const in30 = new Date(); in30.setDate(nowDate.getDate() + 30)

    const expiringSoon = contracts.filter(c => {
      const end = new Date(c.end_date)
      return end >= nowDate && end <= in30 && c.status === 'ativo'
    }).slice(0, 6)

    return { activeContracts, expiringSoon }
  }, [contracts])

  // ── Delinquency data (overdue payments grouped by tenant, enriched with names) ──
  const delinquency = useMemo(() => {
    const overduePayments = payments.filter(p => p.status === 'atrasado')
    const props = propertiesStatus?.properties ?? []
    const byTenant = new Map<number, { tenant_id: number; tenant_name: string; property_name: string; count: number; total: number }>()
    overduePayments.forEach(p => {
      const existing = byTenant.get(p.tenant_id)
      const tenant = tenants.find(t => t.id === p.tenant_id)
      const tenantName = tenant?.name ?? `Inquilino #${p.tenant_id}`
      const prop = props.find(pr => (pr.id || pr.property_id) === p.property_id)
      const propertyName = prop?.property_name || prop?.name || `Imóvel #${p.property_id}`
      if (existing) {
        existing.count += 1
        existing.total += (Number(p.total_amount) || Number(p.amount) || 0)
      } else {
        byTenant.set(p.tenant_id, {
          tenant_id: p.tenant_id,
          tenant_name: tenantName,
          property_name: propertyName,
          count: 1,
          total: (Number(p.total_amount) || Number(p.amount) || 0),
        })
      }
    })
    const list = Array.from(byTenant.values()).sort((a, b) => b.total - a.total)
    return { overdueCount: overduePayments.length, totalOverdue: overduePayments.reduce((s, p) => s + (Number(p.total_amount) || Number(p.amount) || 0), 0), list }
  }, [payments, tenants, propertiesStatus])

  // ── Partial payments (parcial) grouped by tenant ──
  const partialPayments = useMemo(() => {
    const partialPmts = payments.filter(p => p.status === 'parcial')
    const props = propertiesStatus?.properties ?? []
    const byTenant = new Map<number, { tenant_id: number; tenant_name: string; property_name: string; count: number; total: number }>()
    partialPmts.forEach(p => {
      const existing = byTenant.get(p.tenant_id)
      const tenant = tenants.find(t => t.id === p.tenant_id)
      const tenantName = tenant?.name ?? `Inquilino #${p.tenant_id}`
      const prop = props.find(pr => (pr.id || pr.property_id) === p.property_id)
      const propertyName = prop?.property_name || prop?.name || `Imóvel #${p.property_id}`
      if (existing) {
        existing.count += 1
        existing.total += (Number(p.total_amount) || Number(p.amount) || 0)
      } else {
        byTenant.set(p.tenant_id, {
          tenant_id: p.tenant_id,
          tenant_name: tenantName,
          property_name: propertyName,
          count: 1,
          total: (Number(p.total_amount) || Number(p.amount) || 0),
        })
      }
    })
    const list = Array.from(byTenant.values()).sort((a, b) => b.total - a.total)
    return { partialCount: partialPmts.length, list }
  }, [payments, tenants, propertiesStatus])

  // ── Handle finalizar contrato ──
  const handleFinalizarContrato = async (contractId: number) => {
    try {
      await contractsService.updateStatus(contractId, 'inativo')
      toast.success('Contrato finalizado com sucesso')
      await refetchContracts()
      await refetchTenants()
    } catch {
      toast.error('Erro ao finalizar contrato')
    }
  }

  // ── Filter label for chart title ──
  const periodLabel = filterMonth === 'all'
    ? filterYear
    : `${MONTH_NAMES[parseInt(filterMonth) - 1]}/${filterYear}`

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

        {/* ── Filtros Globais ── */}
        <div className="flex flex-wrap gap-3">
          <Select value={filterYear} onValueChange={setFilterYear}>
            <SelectTrigger className="w-[110px]">
              <SelectValue placeholder="Ano" />
            </SelectTrigger>
            <SelectContent>
              {availableYears.map(y => (
                <SelectItem key={y} value={String(y)}>{y}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={filterMonth} onValueChange={setFilterMonth}>
            <SelectTrigger className="w-[130px]">
              <SelectValue placeholder="Mês" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os meses</SelectItem>
              {MONTH_NAMES.map((m, i) => (
                <SelectItem key={i} value={String(i + 1)}>{m}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={filterProperty} onValueChange={setFilterProperty}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Imóvel" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os imóveis</SelectItem>
              {propertyList.map(p => (
                <SelectItem key={p.id} value={String(p.id)}>{p.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={filterCategory} onValueChange={setFilterCategory}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Categoria" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas as categorias</SelectItem>
              {expenseCategories.map(c => (
                <SelectItem key={c} value={c}>{c}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* ═══════════════════════════════════════════════════════════ */}
        {/* BLOCO 1 — Visão Financeira                                 */}
        {/* ═══════════════════════════════════════════════════════════ */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <BarIcon className="h-5 w-5 text-blue-600" />
            <h2 className="text-xl font-semibold">Visão Financeira</h2>
          </div>

          {/* KPI Cards */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">Receita total</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">{currencyFormat(finance.receitaTotal)}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">Despesas totais</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">{currencyFormat(finance.despesasTotal)}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">Lucro / Resultado</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${finance.resultado >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {currencyFormat(finance.resultado)}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts: Despesas donut + Ganhos por Imóvel */}
          <div className="grid gap-6 md:grid-cols-2 mt-6">
            {/* Despesas por Categoria — Donut */}
            <Card>
              <CardHeader>
                <CardTitle>Despesas por Categoria — {periodLabel}</CardTitle>
              </CardHeader>
              <CardContent className="h-80">
                {expensesByCategory.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-muted-foreground">Sem despesas para o período</div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={expensesByCategory} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={95} paddingAngle={2} label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`} labelLine={false}>
                        {expensesByCategory.map((_, idx) => (
                          <Cell key={`exp-${idx}`} fill={DONUT_COLORS[idx % DONUT_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value: number) => currencyFormat(value)} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            {/* Ganhos por Imóvel — Horizontal Bar */}
            <Card>
              <CardHeader>
                <CardTitle>Ganhos por Imóvel — {periodLabel}</CardTitle>
              </CardHeader>
              <CardContent className="h-80">
                {revenueByProperty.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-muted-foreground">Sem receitas para o período</div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={revenueByProperty} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                      <XAxis type="number" tickFormatter={(v: number) => `R$ ${(v / 1000).toFixed(0)}k`} />
                      <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 12 }} />
                      <Tooltip formatter={(value: number) => currencyFormat(value)} />
                      <Bar dataKey="value" name="Receita" fill={BLUE} radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </div>
        </section>

        <Separator />

        {/* ═══════════════════════════════════════════════════════════ */}
        {/* BLOCO 2 — Ocupação de Imóveis                             */}
        {/* ═══════════════════════════════════════════════════════════ */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <PieIcon className="h-5 w-5 text-blue-600" />
            <h2 className="text-xl font-semibold">Ocupação de Imóveis</h2>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Distribuição por Categoria (tipo) — LEFT */}
            <Card>
              <CardHeader className="pb-0">
                <CardTitle className="text-sm">Distribuição por Categoria</CardTitle>
              </CardHeader>
              <CardContent className="h-72 pt-2">
                {typeDistribution.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-muted-foreground text-sm">Nenhum imóvel cadastrado</div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={typeDistribution} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={85} paddingAngle={2} label={({ name, value }) => `${name}: ${value}`} labelLine={false}>
                        {typeDistribution.map((entry, idx) => (
                          <Cell key={`type-${idx}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value: number) => [`${value} imóvel(is)`, 'Quantidade']} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            {/* Pie chart — Ocupação — CENTER */}
            <Card>
              <CardHeader className="pb-0">
                <CardTitle className="text-sm">Status de Ocupação</CardTitle>
              </CardHeader>
              <CardContent className="h-72 pt-2">
                {occupancy.total === 0 ? (
                  <div className="flex items-center justify-center h-full text-muted-foreground text-sm">Nenhum imóvel cadastrado</div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={occupancy.pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={2} fill={BLUE} label={({ name, value }) => `${name}: ${value}`} labelLine={false}>
                        {occupancy.pieData.map((_, idx) => (
                          <Cell key={`cell-${idx}`} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Legend />
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            {/* Info cards — Taxa + Totais — RIGHT */}
            <div className="grid gap-4 content-start">
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Taxa de Ocupação</CardTitle></CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{occupancy.rate}%</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Totais</CardTitle></CardHeader>
                <CardContent className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Imóveis</span>
                    <span className="font-semibold">{occupancy.total}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Ocupados</span>
                    <span className="font-semibold text-blue-600">{occupancy.occupied}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Vagos</span>
                    <span className="font-semibold text-red-600">{occupancy.vacant}</span>
                  </div>
                  {occupancy.maintenance > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Manutenção</span>
                      <span className="font-semibold text-amber-600">{occupancy.maintenance}</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        <Separator />

        {/* ═══════════════════════════════════════════════════════════ */}
        {/* BLOCO 3 — Contratos                                        */}
        {/* ═══════════════════════════════════════════════════════════ */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-xl font-semibold">Contratos</h2>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {/* Contratos ativos — KPI */}
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Contratos ativos</CardTitle></CardHeader>
              <CardContent><div className="text-2xl font-bold text-green-600">{contractsTenants.activeContracts.length}</div></CardContent>
            </Card>

            {/* Próximos a vencer — list */}
            <Card>
              <CardHeader><CardTitle>Próximos a vencer</CardTitle></CardHeader>
              <CardContent>
                {contractsTenants.expiringSoon.length === 0 ? (
                  <p className="text-muted-foreground">Nenhum contrato próximo do vencimento.</p>
                ) : (
                  <ul className="space-y-2">
                    {contractsTenants.expiringSoon.map(c => {
                      const prop = (propertiesStatus?.properties ?? []).find(pr => (pr.id || pr.property_id) === c.property_id)
                      const propName = prop?.property_name || prop?.name || `Imóvel #${c.property_id}`
                      const tenant = tenants.find(t => t.id === c.tenant_id)
                      const tenantName = tenant?.name || `Inquilino #${c.tenant_id}`
                      return (
                        <li key={c.id} className="flex items-center justify-between text-sm gap-2">
                          <span className="flex-1">{propName} • {tenantName}</span>
                          <Badge variant="outline"><Clock className="h-3 w-3 mr-1"/> {new Date(c.end_date).toLocaleDateString()}</Badge>
                          <Button size="sm" variant="destructive" className="ml-2 h-7 text-xs" onClick={() => handleFinalizarContrato(c.id)}>
                            <XCircle className="h-3 w-3 mr-1" /> Finalizar
                          </Button>
                        </li>
                      )
                    })}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>
        </section>

        <Separator />

        {/* ═══════════════════════════════════════════════════════════ */}
        {/* BLOCO 4 — Pagamentos                                       */}
        {/* ═══════════════════════════════════════════════════════════ */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <h2 className="text-xl font-semibold">Pagamentos</h2>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {/* Pagamentos em atraso */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Pagamentos em atraso</span>
                  {delinquency.overdueCount > 0 && (
                    <Badge variant="destructive">{delinquency.overdueCount}</Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {delinquency.list.length === 0 ? (
                  <p className="text-muted-foreground">Nenhum pagamento em atraso.</p>
                ) : (
                  <ul className="space-y-2">
                    {delinquency.list.map(d => (
                      <li key={d.tenant_id} className="flex items-center justify-between text-sm">
                        <div className="flex-1">
                          <span className="font-medium">{d.tenant_name}</span>
                          <span className="text-muted-foreground ml-2">• {d.property_name}</span>
                        </div>
                        <Badge variant="outline" className="mr-2">{d.count} pgto(s)</Badge>
                        <span className="font-semibold text-red-600">{currencyFormat(d.total)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            {/* Pagamentos parciais */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Pagamentos parciais</span>
                  {partialPayments.partialCount > 0 && (
                    <Badge variant="secondary">{partialPayments.partialCount}</Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {partialPayments.list.length === 0 ? (
                  <p className="text-muted-foreground">Nenhum pagamento parcial.</p>
                ) : (
                  <ul className="space-y-2">
                    {partialPayments.list.map(d => (
                      <li key={d.tenant_id} className="flex items-center justify-between text-sm">
                        <div className="flex-1">
                          <span className="font-medium">{d.tenant_name}</span>
                          <span className="text-muted-foreground ml-2">• {d.property_name}</span>
                        </div>
                        <Badge variant="outline" className="mr-2">{d.count} pgto(s)</Badge>
                        <span className="font-semibold text-amber-600">{currencyFormat(d.total)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}