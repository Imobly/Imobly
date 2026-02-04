"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Edit, Trash2, Building2, User, AlertTriangle } from "lucide-react"
import { Payment } from "@/lib/types/payment"
import { useProperties } from "@/lib/hooks/useProperties"
import { useTenants } from "@/lib/hooks/useTenants"

interface PaymentListProps {
  payments: Payment[]
  onEdit: (payment: Payment) => void
  onDelete?: (payment: Payment) => void
}

const statusConfig = {
  paid: { label: "Pago", className: "bg-green-100 text-green-800" },
  pending: { label: "Pendente", className: "bg-yellow-100 text-yellow-800" },
  overdue: { label: "Atrasado", className: "bg-red-100 text-red-800" },
  partial: { label: "Parcial", className: "bg-blue-100 text-blue-800" },
}

export function PaymentList({ payments, onEdit, onDelete }: PaymentListProps) {
  const { properties } = useProperties()
  const { tenants } = useTenants()

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(amount)
  }

  const getDaysOverdue = (dueDate: string) => {
    const today = new Date()
    const due = new Date(dueDate)
    const diffTime = today.getTime() - due.getTime()
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  }
  const formatDateBRShort = (dateStr: string) => {
    const d = new Date(dateStr)
    return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "2-digit" })
  }

  const getProperty = (payment: Payment) => {
    if (payment.property) return payment.property
    return properties.find(p => p.id === payment.property_id)
  }

  const getTenant = (payment: Payment) => {
    if (payment.tenant) return payment.tenant
    return tenants.find(t => t.id === payment.tenant_id)
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Imóvel / Inquilino</TableHead>
            <TableHead>Descrição</TableHead>
            <TableHead>Vencimento</TableHead>
            <TableHead>Pagamento</TableHead>
            <TableHead>Valor</TableHead>
            <TableHead>Multa</TableHead>
            <TableHead>Total</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-[110px]">Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {payments.map((payment) => {
            const property = getProperty(payment)
            const tenant = getTenant(payment)
            
            return (
              <TableRow key={payment.id}>
                <TableCell>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Building2 className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="font-medium text-sm">{property?.name || `Propriedade #${payment.property_id}`}</div>
                        <div className="text-xs text-muted-foreground">{property?.address || "Endereço não disponível"}</div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <User className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="font-medium text-sm">{tenant?.name || `Inquilino #${payment.tenant_id}`}</div>
                        <div className="text-xs text-muted-foreground">{tenant?.email || "Email não disponível"}</div>
                      </div>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="text-sm">{payment.description}</div>
                </TableCell>
                <TableCell>
                  <div className="text-sm">{formatDateBRShort(payment.dueDate)}</div>
                  {payment.status === "overdue" && (
                    <div className="text-xs text-red-600 flex items-center mt-1">
                      <AlertTriangle className="h-3 w-3 mr-1" />
                      {getDaysOverdue(payment.dueDate)} dias em atraso
                    </div>
                  )}
                </TableCell>
                <TableCell>
                  {payment.paymentDate ? (
                    <div className="text-sm">{formatDateBRShort(payment.paymentDate)}</div>
                  ) : (
                    <div className="text-xs text-muted-foreground">Não pago</div>
                  )}
                </TableCell>
                <TableCell>
                  <div className="text-sm font-medium">{formatCurrency(payment.amount)}</div>
                </TableCell>
                <TableCell>
                  {payment.fineAmount > 0 ? (
                    <div className="text-sm text-red-600">{formatCurrency(payment.fineAmount)}</div>
                  ) : (
                    <div className="text-xs text-muted-foreground">-</div>
                  )}
                </TableCell>
                <TableCell>
                  <div className="text-sm font-semibold">{formatCurrency(payment.totalAmount)}</div>
                </TableCell>
                <TableCell>
                  <Badge 
                    className={statusConfig[payment.status as keyof typeof statusConfig]?.className}
                  >
                    {statusConfig[payment.status as keyof typeof statusConfig]?.label || payment.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => onEdit(payment)}>
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:text-red-700"
                      onClick={() => onDelete && onDelete(payment)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}