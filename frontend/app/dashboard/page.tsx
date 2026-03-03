'use client'

import { useState, useMemo } from 'react'
import { ProtectedRoute } from '../../components/auth/protected-route'
import { DashboardLayout } from '../../components/dashboard-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { currencyFormat } from '@/lib/utils'
import { usePropertiesStatus, useDashboard } from '@/lib/hooks/useDashboard'
import { usePayments } from '@/lib/hooks/usePayments'
import { useExpenses } from '@/lib/hooks/useExpenses'
import { useContracts } from '@/lib/hooks/useContracts'
import { useTenants } from '@/lib/hooks/useTenants'
import { PieChart as PieIcon, BarChart as BarIcon, Clock } from 'lucide-react'
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

export default function DashboardPage() {
  // Data hooks
  const { data: propertiesStatus, loading: propertiesLoading } = usePropertiesStatus()
  const { summary } = useDashboard()
  const { payments } = usePayments()
  const { expenses } = useExpenses()
  const { contracts } = useContracts()
  const { tenants } = useTenants()

  // ── Filter state ──
  const now = new Date()
  const [filterYear, setFilterYear] = useState<string>(String(now.getFullYear()))
  const [filterMonth, setFilterMonth] = useState<string>('all') // 'all' or '1'-'12'
  const [filterProperty, setFilterProperty] = useState<string>('all')
  const [filterCategory, setFilterCategory] = useState<string>('all')

  // Available years (from payments/expenses, or just current +-1)
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

    // Filter payments → revenue (paid only)
    const filteredPayments = payments.filter(p => {
      if (p.status !== 'paid') return false
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

    // Build chart rows: group by month
    const monthlyMap = new Map<number, { revenue: number; expenses: number }>()

    // Determine which months to show
    const monthsToShow: number[] = []
    if (filterMonth !== 'all') {
      monthsToShow.push(parseInt(filterMonth))
    } else {
      for (let m = 1; m <= 12; m++) monthsToShow.push(m)
    }

    monthsToShow.forEach(m => monthlyMap.set(m, { revenue: 0, expenses: 0 }))

    filteredPayments.forEach(p => {
      const pDate = p.payment_date ? new Date(p.payment_date) : new Date(p.due_date)
      const m = pDate.getMonth() + 1
      const entry = monthlyMap.get(m)
      if (entry) entry.revenue += (p.total_amount || p.amount || 0)
    })

    filteredExpenses.forEach(e => {
      const eDate = new Date(e.date)
      const m = eDate.getMonth() + 1
      const entry = monthlyMap.get(m)
      if (entry) entry.expenses += (Number(e.amount) || 0)
    })

    const chartRows = monthsToShow.map(m => ({
      name: MONTH_NAMES[m - 1],
      receitas: monthlyMap.get(m)?.revenue ?? 0,
      despesas: monthlyMap.get(m)?.expenses ?? 0,
    }))

    return { receitaTotal, despesasTotal, resultado, chartRows }
  }, [payments, expenses, filterYear, filterMonth, filterProperty, filterCategory])

  // ── Occupancy metrics (fixed: also consider tenant_id) ──
  const occupancy = useMemo(() => {
    const props = propertiesStatus?.properties ?? []
    const total = props.length
    // Property is occupied if status is 'occupied' OR tenant_id is set
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

  // ── Contracts & tenants (untouched) ──
  const contractsTenants = useMemo(() => {
    const activeContracts = contracts.filter(c => c.status === 'active')
    const activeTenants = tenants.filter(t => t.status === 'active')
    const nowDate = new Date()
    const in30 = new Date(); in30.setDate(nowDate.getDate() + 30)
    const last30 = new Date(); last30.setDate(nowDate.getDate() - 30)

    const expiringSoon = contracts.filter(c => {
      const end = new Date(c.end_date)
      return end >= nowDate && end <= in30 && c.status === 'active'
    }).slice(0, 6)

    const recentlyEnded = contracts.filter(c => {
      const end = new Date(c.end_date)
      return end < nowDate && end >= last30 && (c.status === 'expired' || c.status === 'terminated')
    }).slice(0, 6)

    return { activeContracts, activeTenants, expiringSoon, recentlyEnded }
  }, [contracts, tenants])

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

        {/* ═══════════════════════════════════════════════════════════ */}
        {/* BLOCO 1 — Visão Financeira                                 */}
        {/* ═══════════════════════════════════════════════════════════ */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <BarIcon className="h-5 w-5 text-blue-600" />
            <h2 className="text-xl font-semibold">Visão Financeira</h2>
          </div>

          {/* Filtros */}
          <div className="flex flex-wrap gap-3 mb-4">
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

          {/* KPI Cards — apenas 3 */}
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

          {/* Gráfico Receita x Despesas */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Receitas vs. Despesas — {periodLabel}</CardTitle>
            </CardHeader>
            <CardContent className="h-80">
              {finance.chartRows.length === 0 ? (
                <div className="flex items-center justify-center h-full text-muted-foreground">Sem dados para o período selecionado</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={finance.chartRows} barGap={4}>
                    <XAxis dataKey="name" />
                    <YAxis tickFormatter={(v: number) => `R$ ${(v / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(value: number) => currencyFormat(value)} />
                    <Legend />
                    <Bar dataKey="receitas" name="Receitas" fill={BLUE} radius={[4, 4, 0, 0]} />
                    <Bar dataKey="despesas" name="Despesas" fill={RED} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
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
            {/* Pie chart — Ocupação */}
            <Card>
              <CardHeader className="pb-0">
                <CardTitle className="text-sm">Status de Ocupação</CardTitle>
              </CardHeader>
              <CardContent className="h-72 pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={occupancy.pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={2}>
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

            {/* Info cards — Taxa + Totais */}
            <div className="grid gap-4 content-start">
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Taxa de Ocupação</CardTitle></CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{occupancy.rate}%</div>
                  <div className="text-xs text-muted-foreground mt-1">{occupancy.occupied} de {occupancy.total} imóveis ocupados</div>
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

            {/* Horizontal bar chart — Distribuição por categoria (tipo) */}
            <Card>
              <CardHeader className="pb-0">
                <CardTitle className="text-sm">Distribuição por Categoria</CardTitle>
              </CardHeader>
              <CardContent className="h-72 pt-2">
                {typeDistribution.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-muted-foreground text-sm">Nenhum imóvel cadastrado</div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={typeDistribution} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                      <XAxis type="number" allowDecimals={false} />
                      <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 12 }} />
                      <Tooltip formatter={(value: number) => [`${value} imóvel(is)`, 'Quantidade']} />
                      <Bar dataKey="value" name="Quantidade" radius={[0, 4, 4, 0]}>
                        {typeDistribution.map((entry, idx) => (
                          <Cell key={`type-${idx}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </div>
        </section>

        <Separator />

        {/* ═══════════════════════════════════════════════════════════ */}
        {/* BLOCO 3 — Contratos & Inquilinos (inalterado)              */}
        {/* ═══════════════════════════════════════════════════════════ */}
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
      </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}