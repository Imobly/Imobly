"use client"

import { useState, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Plus, Search, AlertTriangle, TrendingUp, CheckCircle, Clock, XCircle, RefreshCw, DollarSign } from "lucide-react"
import { usePayments } from "@/lib/hooks/usePayments"
import { useProperties } from "@/lib/hooks/useProperties"
import { useTenants } from "@/lib/hooks/useTenants"
import { PaymentDialog } from "./payment-dialog"
import { PaymentList } from "./payment-list"
import { PaymentCreate, PaymentResponse } from "@/lib/types/api"
import { convertApiToPayment, Payment } from "@/lib/types/payment"
import { EmptyState } from "@/components/ui/empty-state"
import { currencyFormat } from "@/lib/utils"

const MONTH_NAMES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

export function PaymentsView() {
  const { payments, loading, error, refetch, createPayment, confirmPayment, deletePayment } = usePayments()
  const { properties } = useProperties()
  const { tenants } = useTenants()

  const [searchTerm, setSearchTerm] = useState("")
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedPayment, setSelectedPayment] = useState<any>(null)

  // Filter state
  const now = new Date()
  const [filterStatus, setFilterStatus] = useState<string>("all")
  const [filterProperty, setFilterProperty] = useState<string>("all")
  const [filterTenant, setFilterTenant] = useState<string>("all")
  const [filterMonth, setFilterMonth] = useState<string>("all")
  const [filterYear, setFilterYear] = useState<string>(String(now.getFullYear()))

  // Available years from payment data
  const availableYears = useMemo(() => {
    const years = new Set<number>()
    payments.forEach(p => { if (p.due_date) years.add(new Date(p.due_date).getFullYear()) })
    years.add(now.getFullYear())
    return Array.from(years).sort((a, b) => b - a)
  }, [payments])

  // Mostrar loading
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <div>
          <h2 className="text-xl font-semibold text-center">Carregando Pagamentos</h2>
          <p className="text-gray-500 text-center mt-2">Aguarde um momento...</p>
        </div>
      </div>
    )
  }

  // Mostrar erro
  if (error) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Erro ao carregar pagamentos"
        description={`Não foi possível carregar a lista de pagamentos. ${error}`}
        action={{
          label: "Tentar novamente",
          onClick: refetch
        }}
        variant="error"
      />
    )
  }

  // Converter dados da API para o formato interno
  const convertedPayments = payments.map(convertApiToPayment)

  // Apply all filters
  const filteredPayments = convertedPayments.filter((payment: Payment) => {
    // Year filter
    if (filterYear !== "all") {
      const dueDate = payment.dueDate ? new Date(payment.dueDate) : null
      if (!dueDate || dueDate.getFullYear() !== parseInt(filterYear)) return false
    }
    // Month filter
    if (filterMonth !== "all") {
      const dueDate = payment.dueDate ? new Date(payment.dueDate) : null
      if (!dueDate || dueDate.getMonth() + 1 !== parseInt(filterMonth)) return false
    }
    // Property filter
    if (filterProperty !== "all" && String(payment.property_id) !== filterProperty) return false
    // Tenant filter
    if (filterTenant !== "all" && String(payment.tenant_id) !== filterTenant) return false
    // Status filter
    if (filterStatus !== "all" && payment.status !== filterStatus) return false
    // Search term
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      const matchesSearch =
        payment.description?.toLowerCase().includes(term) ||
        payment.property_id.toString().includes(term) ||
        payment.tenant_id.toString().includes(term)
      if (!matchesSearch) return false
    }
    return true
  })

  // Compute status counts & amounts from filtered payments
  const statusCounts = {
    total: filteredPayments.length,
    paid: filteredPayments.filter((p) => p.status === "pago").length,
    pending: filteredPayments.filter((p) => p.status === "pendente").length,
    partial: filteredPayments.filter((p) => p.status === "parcial").length,
    overdue: filteredPayments.filter((p) => p.status === "atrasado").length,
  }

  const totalAmount = filteredPayments.reduce((s, p) => s + (p.totalAmount || 0), 0)
  const paidAmount = filteredPayments
    .filter((p) => p.status === "pago")
    .reduce((s, p) => s + (p.totalAmount || 0), 0)
  const pendingAmount = filteredPayments
    .filter((p) => p.status === "pendente")
    .reduce((s, p) => s + (p.totalAmount || 0), 0)
  const overdueAmount = filteredPayments
    .filter((p) => p.status === "atrasado")
    .reduce((s, p) => s + (p.totalAmount || 0), 0)

  const handleCreatePayment = () => {
    setSelectedPayment(null)
    setIsDialogOpen(true)
  }

  const handleEditPayment = (payment: any) => {
    setSelectedPayment(payment)
    setIsDialogOpen(true)
  }

  const handleSavePayment = async () => {
    try {
      // O diálogo já registra/edita o pagamento via serviço; aqui apenas refazemos o fetch
      setIsDialogOpen(false)
      await refetch()
    } catch (error) {
      console.error("Erro ao salvar pagamento:", error)
    }
  }

  const handleDeletePayment = async (payment: any) => {
    if (!payment?.id) return
    const confirmed = window.confirm("Tem certeza que deseja excluir este pagamento?")
    if (!confirmed) return
    const success = await deletePayment(payment.id)
    if (!success) return
  }

  const handleConfirmPayment = async (paymentId: number) => {
    try {
      const success = await confirmPayment(paymentId)
      if (success) {
        refetch()
      }
    } catch (error) {
      console.error("Erro ao confirmar pagamento:", error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Pagamentos</h1>
          <p className="text-gray-600">Gerencie pagamentos e aluguéis</p>
        </div>
        <Button 
          className="bg-blue-600 hover:bg-blue-700"
          onClick={handleCreatePayment}
        >
          <Plus className="mr-2 h-4 w-4" />
          Novo Pagamento
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Select value={filterYear} onValueChange={setFilterYear}>
          <SelectTrigger className="w-[110px]">
            <SelectValue placeholder="Ano" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            {availableYears.map(y => (
              <SelectItem key={y} value={String(y)}>{y}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={filterMonth} onValueChange={setFilterMonth}>
          <SelectTrigger className="w-[140px]">
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
            {properties.map(p => (
              <SelectItem key={p.id} value={String(p.id)}>{p.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={filterTenant} onValueChange={setFilterTenant}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Inquilino" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os inquilinos</SelectItem>
            {tenants.map(t => (
              <SelectItem key={t.id} value={String(t.id)}>{t.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="pago">Pago</SelectItem>
            <SelectItem value="pendente">Pendente</SelectItem>
            <SelectItem value="atrasado">Atrasado</SelectItem>
            <SelectItem value="parcial">Parcial</SelectItem>
          </SelectContent>
        </Select>

        <div className="flex-1 min-w-[200px] max-w-sm">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar pagamentos..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total de Pagamentos</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statusCounts.total}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pagos</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{statusCounts.paid}</div>
            <p className="text-xs text-muted-foreground">
              {currencyFormat(paidAmount)} recebidos
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pendentes</CardTitle>
            <Clock className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{statusCounts.pending}</div>
            <p className="text-xs text-muted-foreground">
              {currencyFormat(pendingAmount)} pendentes
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Em Atraso</CardTitle>
            <XCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{statusCounts.overdue}</div>
            <p className="text-xs text-muted-foreground">
              {currencyFormat(overdueAmount)} em atraso
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Content */}
      {payments.length === 0 ? (
        <EmptyState
          icon={DollarSign}
          title="Nenhum pagamento cadastrado"
          description="Comece registrando seu primeiro pagamento de aluguel."
          action={{
            label: "Adicionar Primeiro Pagamento",
            onClick: handleCreatePayment
          }}
        />
      ) : filteredPayments.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <AlertTriangle className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">Nenhum pagamento encontrado</h3>
            <p className="text-gray-500 text-center mb-4">
              Tente ajustar os filtros ou termos de busca
            </p>
          </CardContent>
        </Card>
      ) : (
        <PaymentList
          payments={filteredPayments}
          onEdit={handleEditPayment}
          onDelete={handleDeletePayment}
        />
      )}

      {/* Payment Dialog */}
      <PaymentDialog
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        payment={selectedPayment}
        onSave={handleSavePayment}
      />
    </div>
  )
}