"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Plus, Search, Filter, AlertTriangle, TrendingUp, CheckCircle, Clock, XCircle, RefreshCw, DollarSign } from "lucide-react"
import { usePayments } from "@/lib/hooks/usePayments"
import { PaymentDialog } from "./payment-dialog"
import { PaymentList } from "./payment-list"
import { PaymentCreate, PaymentResponse } from "@/lib/types/api"
import { convertApiToPayment, Payment } from "@/lib/types/payment"
import { EmptyState } from "@/components/ui/empty-state"
import { currencyFormat } from "@/lib/utils"



export function PaymentsView() {
  const { payments, loading, error, refetch, createPayment, confirmPayment, deletePayment } = usePayments()
  const [searchTerm, setSearchTerm] = useState("")
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedPayment, setSelectedPayment] = useState<any>(null)

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

  const filteredPayments = convertedPayments.filter((payment: Payment) => {
    const matchesSearch = 
      payment.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      payment.property_id.toString().includes(searchTerm.toLowerCase()) ||
      payment.tenant_id.toString().includes(searchTerm.toLowerCase())
    return matchesSearch
  })

  const statusCounts = {
    total: payments.length,
    paid: payments.filter((p) => p.status === "paid").length,
    pending: payments.filter((p) => p.status === "pending").length,
    partial: payments.filter((p) => p.status === "partial").length,
    overdue: payments.filter((p) => p.status === "overdue").length,
  }

  const totalAmount = payments.reduce((sum, payment) => sum + payment.total_amount, 0)
  const paidAmount = payments
    .filter((p) => p.status === "paid")
    .reduce((sum, payment) => sum + payment.total_amount, 0)
  const pendingAmount = payments
    .filter((p) => p.status === "pending" || p.status === "partial" || p.status === "overdue")
    .reduce((sum, payment) => sum + payment.total_amount, 0)

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

      {/* Status Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total de Pagamentos</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statusCounts.total}</div>
            <p className="text-xs text-muted-foreground">
              {currencyFormat(totalAmount)} no total
            </p>
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
              Aguardando pagamento
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
              {currencyFormat(pendingAmount)} pendentes
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Controls */}
      <div className="flex items-center gap-4">
        <div className="flex-1 max-w-sm">
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

        <Button variant="outline" size="sm">
          <Filter className="mr-2 h-4 w-4" />
          Filtros
        </Button>
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