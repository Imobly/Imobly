"use client"

import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Building2, User, Calendar, CreditCard, MoreHorizontal, Edit, Trash2, Eye, AlertTriangle } from "lucide-react"
import { Payment } from "@/lib/types/payment"
import { useProperties } from "@/lib/hooks/useProperties"
import { useTenants } from "@/lib/hooks/useTenants"
import { useMemo } from "react"
import { formatCurrency, formatDate } from '@/lib/utils/format'

interface PaymentCardProps {
  payment: Payment
  onEdit: (payment: Payment) => void
}

const statusConfig = {
  pago: { label: "Pago", className: "bg-green-100 text-green-800" },
  pendente: { label: "Pendente", className: "bg-yellow-100 text-yellow-800" },
  parcial: { label: "Parcial", className: "bg-orange-100 text-orange-800" },
  atrasado: { label: "Atrasado", className: "bg-red-100 text-red-800" },
}

const paymentMethodConfig = {
  pix: "PIX",
  bank_transfer: "Transferência",
  cash: "Dinheiro",
  check: "Cheque",
  credit_card: "Cartão de Crédito",
}

export function PaymentCard({ payment, onEdit }: PaymentCardProps) {
  const { properties } = useProperties()
  const { tenants } = useTenants()

  // Buscar dados da propriedade e inquilino pelos IDs
  const property = useMemo(() => {
    if (payment.property) return payment.property
    return properties.find(p => p.id === payment.property_id)
  }, [payment.property, payment.property_id, properties])

  const tenant = useMemo(() => {
    if (payment.tenant) return payment.tenant
    return tenants.find(t => t.id === payment.tenant_id)
  }, [payment.tenant, payment.tenant_id, tenants])

  // Os dias de atraso vêm do servidor, junto do saldo. Recalcular aqui com
  // `new Date()` dava resultado diferente do backend na virada do dia, porque
  // o backend trabalha no fuso de São Paulo e o navegador no fuso do usuário.
  const diasDeAtraso = payment.daysOverdue ?? 0

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <Badge
                variant="secondary"
                className={statusConfig[payment.status as keyof typeof statusConfig].className}
              >
                {statusConfig[payment.status as keyof typeof statusConfig].label}
              </Badge>
              {diasDeAtraso > 0 && payment.balanceAmount > 0 && (
                <Badge variant="secondary" className="bg-red-100 text-red-800 flex items-center">
                  <AlertTriangle className="mr-1 h-3 w-3" />
                  {diasDeAtraso} dias
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">{payment.description}</p>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit(payment)}>
                <Edit className="mr-2 h-4 w-4" />
                Editar
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Eye className="mr-2 h-4 w-4" />
                Visualizar
              </DropdownMenuItem>
              <DropdownMenuItem className="text-red-600">
                <Trash2 className="mr-2 h-4 w-4" />
                Excluir
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        <div className="flex items-center text-sm">
          <Building2 className="mr-2 h-3 w-3 text-muted-foreground" />
          <div>
            <div className="font-medium">{property?.name || `Propriedade #${payment.property_id}`}</div>
            <div className="text-xs text-muted-foreground">{property?.address || "Endereço não disponível"}</div>
          </div>
        </div>

        <div className="flex items-center text-sm">
          <User className="mr-2 h-3 w-3 text-muted-foreground" />
          <div>
            <div className="font-medium">{tenant?.name || `Inquilino #${payment.tenant_id}`}</div>
            <div className="text-xs text-muted-foreground">{tenant?.email || "Email não disponível"}</div>
          </div>
        </div>

        <div className="flex items-center text-sm text-muted-foreground">
          <Calendar className="mr-2 h-3 w-3" />
          <div>
            <div>Vencimento: {formatDate(payment.dueDate)}</div>
            {payment.paymentDate && <div>Pagamento: {formatDate(payment.paymentDate)}</div>}
          </div>
        </div>

        {payment.paymentMethod && (
          <div className="flex items-center text-sm">
            <CreditCard className="mr-2 h-3 w-3 text-muted-foreground" />
            {paymentMethodConfig[payment.paymentMethod as keyof typeof paymentMethodConfig]}
          </div>
        )}

        <div className="space-y-1 pt-2 border-t">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Valor:</span>
            <span>{formatCurrency(payment.amount)}</span>
          </div>
          {payment.fineAmount > 0 && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Multa:</span>
              <span className="text-red-600">{formatCurrency(payment.fineAmount)}</span>
            </div>
          )}
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Total devido:</span>
            <span>{formatCurrency(payment.totalAmount)}</span>
          </div>
          {payment.paidAmount > 0 && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Recebido:</span>
              <span className="text-green-700">
                {formatCurrency(payment.paidAmount)}
              </span>
            </div>
          )}
          {/* O saldo é o que ainda se cobra. O card antigo mostrava só um
              "Total" que, em pagamento parcial, era o valor JÁ PAGO. */}
          <div className="flex justify-between font-bold">
            <span>{payment.balanceAmount > 0 ? "Saldo devedor:" : "Quitado"}</span>
            <span className={payment.balanceAmount > 0 ? "text-red-600" : "text-green-700"}>
              {formatCurrency(payment.balanceAmount)}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
