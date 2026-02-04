"use client"

import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Edit, Trash2, FileText, Calendar, MapPin, User, AlertTriangle } from "lucide-react"
import { useProperties } from "@/lib/hooks/useProperties"

interface Expense {
  id: string
  type: "expense" | "maintenance"
  category: string
  description: string
  amount: number
  date: string
  property: string
  status: "pending" | "paid" | "scheduled"
  priority?: "low" | "medium" | "high" | "urgent"
  vendor?: string
  receipt?: string
  notes?: string
}

interface ExpenseCardProps {
  expenses: Expense[]
  onEdit: (expense: Expense) => void
  onDelete: (id: string) => void
}

export function ExpenseCard({ expenses, onEdit, onDelete }: ExpenseCardProps) {
  const { properties } = useProperties()
  const getPropertyInfo = (expense: Expense) => {
    if (expense.property) return expense.property
    const found = properties.find(p => p.id === (expense as any).property_id)
    return found ? `${found.name} — ${found.address}` : (expense as any).property_id ? `Propriedade #${(expense as any).property_id}` : "—"
  }
  const getStatusColor = (status: string) => {
    switch (status) {
      case "paid":
        return "bg-success text-success-foreground"
      case "pending":
        return "bg-warning text-warning-foreground"
      case "scheduled":
        return "bg-blue-500 text-white"
      default:
        return "bg-muted text-muted-foreground"
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "paid":
        return "Pago"
      case "pending":
        return "Pendente"
      case "scheduled":
        return "Agendado"
      default:
        return status
    }
  }

  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case "urgent":
        return "bg-danger text-danger-foreground"
      case "high":
        return "bg-orange-500 text-white"
      case "medium":
        return "bg-warning text-warning-foreground"
      case "low":
        return "bg-blue-500 text-white"
      default:
        return "bg-muted text-muted-foreground"
    }
  }

  const getPriorityText = (priority?: string) => {
    switch (priority) {
      case "urgent":
        return "Urgente"
      case "high":
        return "Alta"
      case "medium":
        return "Média"
      case "low":
        return "Baixa"
      default:
        return ""
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {expenses.map((expense) => (
        <Card key={expense.id} className="hover:shadow-md transition-shadow">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Badge variant={expense.type === "maintenance" ? "secondary" : "outline"}>
                    {expense.type === "maintenance" ? "Manutenção" : "Despesa"}
                  </Badge>
                  {expense.priority && (
                    <Badge className={getPriorityColor(expense.priority)}>
                      {expense.priority === "urgent" && <AlertTriangle className="h-3 w-3 mr-1" />}
                      {getPriorityText(expense.priority)}
                    </Badge>
                  )}
                </div>
                <h3 className="font-semibold text-lg">{expense.category}</h3>
                <p className="text-sm text-muted-foreground">{expense.description}</p>
              </div>
              <Badge className={getStatusColor(expense.status)}>{getStatusText(expense.status)}</Badge>
            </div>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="text-2xl font-bold text-foreground">
              {new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(expense.amount)}
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Calendar className="h-4 w-4" />
                {new Date(expense.date).toLocaleDateString("pt-BR")}
              </div>

              <div className="flex items-center gap-2 text-muted-foreground">
                <MapPin className="h-4 w-4" />
                {getPropertyInfo(expense)}
              </div>

              {expense.vendor && (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <User className="h-4 w-4" />
                  {expense.vendor}
                </div>
              )}

              {expense.receipt && (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <FileText className="h-4 w-4" />
                  Comprovante anexado
                </div>
              )}
            </div>

            {expense.notes && (
              <div className="p-2 bg-muted rounded text-sm">
                <strong>Observações:</strong> {expense.notes}
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => onEdit(expense)} className="flex-1">
                <Edit className="h-4 w-4 mr-2" />
                Editar
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDelete(expense.id)}
                className="text-danger hover:text-danger"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
