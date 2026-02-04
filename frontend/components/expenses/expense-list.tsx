"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Edit, Trash2, FileText, AlertTriangle } from "lucide-react"
import { useProperties } from "@/lib/hooks/useProperties"

interface Expense {
  id: string
  type: "expense" | "maintenance"
  category: string
  description: string
  amount: number
  date: string
  property?: string
  property_id?: number
  status: "pending" | "paid" | "scheduled"
  priority?: "low" | "medium" | "high" | "urgent"
  vendor?: string
  receipt?: string
  notes?: string
}

interface ExpenseListProps {
  expenses: Expense[]
  onEdit: (expense: Expense) => void
  onDelete: (id: string) => void
}

export function ExpenseList({ expenses, onEdit, onDelete }: ExpenseListProps) {
  const { properties } = useProperties()
  const formatCurrency = (amount: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(amount)
  const getPropertyInfo = (expense: Expense) => {
    if (expense.property) return expense.property
    const found = properties.find(p => p.id === expense.property_id)
    return found ? `${found.name} — ${found.address}` : expense.property_id ? `Propriedade #${expense.property_id}` : "—"
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
    <Card>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="border-b bg-muted/50">
              <tr>
                <th className="text-left p-4 font-medium">Tipo/Categoria</th>
                <th className="text-left p-4 font-medium">Descrição</th>
                <th className="text-left p-4 font-medium">Valor</th>
                <th className="text-left p-4 font-medium">Data</th>
                <th className="text-left p-4 font-medium">Imóvel</th>
                <th className="text-left p-4 font-medium">Status</th>
                <th className="text-left p-4 font-medium">Ações</th>
              </tr>
            </thead>
            <tbody>
              {expenses.map((expense) => (
                <tr key={expense.id} className="border-b hover:bg-muted/50">
                  <td className="p-4">
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
                      <div className="font-medium">{expense.category}</div>
                      {expense.vendor && <div className="text-sm text-muted-foreground">{expense.vendor}</div>}
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="space-y-1">
                      <div>{expense.description}</div>
                      {expense.receipt && (
                        <div className="flex items-center gap-1 text-sm text-muted-foreground">
                          <FileText className="h-3 w-3" />
                          Comprovante
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="p-4 font-semibold">
                    {formatCurrency(expense.amount)}
                  </td>
                  <td className="p-4">{new Date(expense.date).toLocaleDateString("pt-BR")}</td>
                  <td className="p-4 text-sm">{getPropertyInfo(expense)}</td>
                  <td className="p-4">
                    <Badge className={getStatusColor(expense.status)}>{getStatusText(expense.status)}</Badge>
                  </td>
                  <td className="p-4">
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => onEdit(expense)}>
                        <Edit className="h-4 w-4" />
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
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
