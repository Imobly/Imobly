"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Plus, Search, Grid3X3, List, TrendingUp, DollarSign, AlertTriangle, Edit, Trash2, RefreshCw, Receipt } from "lucide-react"
import { useExpenses } from "@/lib/hooks/useExpenses"
import { useProperties } from "@/lib/hooks/useProperties"
import { ExpenseDialog } from "@/components/expenses/expense-dialog"
import { EmptyState } from "@/components/ui/empty-state"
import { currencyFormat } from "@/lib/utils"

export function ExpensesView() {
  const [searchTerm, setSearchTerm] = useState("")
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
  const [showDialog, setShowDialog] = useState(false)
  const [selectedExpense, setSelectedExpense] = useState<any | null>(null)
  
  const { expenses, loading, error, refetch, createExpense, updateExpense, deleteExpense } = useExpenses()
  const { properties } = useProperties()

  // Mostrar loading
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <div>
          <h2 className="text-xl font-semibold text-center">Carregando Despesas</h2>
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
        title="Erro ao carregar despesas"
        description={`Não foi possível carregar a lista de despesas. ${error}`}
        action={{
          label: "Tentar novamente",
          onClick: refetch
        }}
        variant="error"
      />
    )
  }

  const filteredExpenses = expenses.filter((expense) => {
    const matchesSearch = 
      expense.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      expense.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (expense.vendor && expense.vendor.toLowerCase().includes(searchTerm.toLowerCase()))
    return matchesSearch
  })

  const statusCounts = {
    total: expenses.length,
    paid: expenses.filter((e) => e.status === "paid").length,
    pending: expenses.filter((e) => e.status === "pending").length,
    scheduled: expenses.filter((e) => e.status === "scheduled").length,
  }

  const totalAmount = expenses.reduce((sum, expense) => sum + Number(expense.amount), 0)
  const paidAmount = expenses
    .filter((e) => e.status === "paid")
    .reduce((sum, expense) => sum + Number(expense.amount), 0)
  const pendingAmount = expenses
    .filter((e) => e.status === "pending")
    .reduce((sum, expense) => sum + Number(expense.amount), 0)

  const urgentExpenses = expenses.filter((e) => e.priority === "urgent").length

  const handleAdd = () => {
    setSelectedExpense(null)
    setShowDialog(true)
  }

  const handleEdit = (expense: any) => {
    setSelectedExpense(expense)
    setShowDialog(true)
  }

  const handleSave = async (expenseData: any) => {
    try {
      console.log("💾 Salvando despesa:", expenseData)
      
      if (selectedExpense) {
        const result = await updateExpense(selectedExpense.id, expenseData)
        console.log("✅ Despesa atualizada:", result)
      } else {
        const result = await createExpense(expenseData)
        console.log("✅ Despesa criada:", result)
      }
      
      setShowDialog(false)
      setSelectedExpense(null)
      await refetch()
    } catch (error) {
      console.error('❌ Erro ao salvar despesa:', error)
    }
  }

  const handleDelete = async (expenseId: string) => {
    if (confirm('Tem certeza que deseja deletar esta despesa?')) {
      await deleteExpense(expenseId)
    }
  }

  return (
    <div className="space-y-6">
      {/* Action Button */}
      <div className="flex justify-end">
        <Button onClick={handleAdd} className="bg-blue-600 hover:bg-blue-700">
          <Plus className="mr-2 h-4 w-4" />
          Nova Despesa
        </Button>
      </div>

      {/* Status Card */}
      <Card className="max-w-md">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground">Total gasto em despesas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="h-4 w-4 rounded-full bg-red-500" />
            <div className="text-3xl font-bold text-foreground">
              {totalAmount.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Search and Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="Buscar despesas..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant={viewMode === "grid" ? "default" : "outline"}
            size="sm"
            onClick={() => setViewMode("grid")}
          >
            <Grid3X3 className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === "list" ? "default" : "outline"}
            size="sm"
            onClick={() => setViewMode("list")}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="space-y-6">
        {expenses.length === 0 ? (
          <EmptyState
            icon={Receipt}
            title="Nenhuma despesa cadastrada"
            description="Comece registrando sua primeira despesa ou manutenção."
            action={{
              label: "Adicionar Primeira Despesa",
              onClick: handleAdd
            }}
          />
        ) : filteredExpenses.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Nenhuma despesa encontrada com os filtros aplicados.</p>
          </div>
        ) : viewMode === "list" ? (
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b bg-muted/50">
                  <tr>
                    <th className="text-left p-3 text-sm font-medium">Categoria</th>
                    <th className="text-right p-3 text-sm font-medium">Valor</th>
                    <th className="text-center p-3 text-sm font-medium">Propriedade</th>
                    <th className="text-center p-3 text-sm font-medium">Status</th>
                    <th className="text-center p-3 text-sm font-medium">Data</th>
                    <th className="text-center p-3 text-sm font-medium">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredExpenses.map((expense) => {
                    const property = properties.find(p => p.id === expense.property_id)
                    return (
                    <tr key={expense.id} className="border-b hover:bg-muted/50 transition-colors">
                      <td className="p-3">
                        <div>
                          <p className="font-medium text-sm">{expense.category}</p>
                          <p className="text-xs text-muted-foreground">{expense.description}</p>
                        </div>
                      </td>
                      <td className="p-3 text-right font-semibold">
                        {expense.amount.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                      </td>
                      <td className="p-3 text-center">
                        <span className="text-sm">{property?.name || 'N/A'}</span>
                      </td>
                      <td className="p-3 text-center">
                        <span className={`px-2 py-1 rounded text-xs font-medium inline-block ${
                          expense.status === 'paid' ? 'bg-green-100 text-green-800' :
                          expense.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {expense.status === 'paid' ? 'Paga' :
                           expense.status === 'pending' ? 'Pendente' : 'Agendada'}
                        </span>
                      </td>
                      <td className="p-3 text-center text-sm">
                        {new Date(expense.date).toLocaleDateString('pt-BR')}
                      </td>
                      <td className="p-3 text-center">
                        <div className="flex gap-1 justify-center">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(expense)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(expense.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  )})}
                </tbody>
              </table>
            </div>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredExpenses.map((expense) => (
              <Card key={expense.id} className="p-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-start">
                    <h3 className="font-medium">{expense.description}</h3>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(expense)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(expense.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      expense.status === 'paid' ? 'bg-green-100 text-green-800' :
                      expense.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {expense.status === 'paid' ? 'Paga' :
                       expense.status === 'pending' ? 'Pendente' : 'Agendada'}
                    </span>
                    {expense.priority && (
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        expense.priority === 'urgent' ? 'bg-red-100 text-red-800' :
                        expense.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                        expense.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {expense.priority === 'urgent' ? 'Urgente' :
                         expense.priority === 'high' ? 'Alta' :
                         expense.priority === 'medium' ? 'Média' : 'Baixa'}
                      </span>
                    )}
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-gray-600">Categoria: {expense.category}</p>
                    <p className="text-lg font-semibold">
                      {expense.amount.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                    </p>
                    <p className="text-sm text-gray-500">
                      Data: {new Date(expense.date).toLocaleDateString('pt-BR')}
                    </p>
                    <p className="text-sm text-gray-500">
                      Propriedade ID: {expense.property_id}
                    </p>
                    {expense.vendor && (
                      <p className="text-sm text-gray-600">Fornecedor: {expense.vendor}</p>
                    )}
                    {expense.number && (
                      <p className="text-sm text-gray-600">Contato: {expense.number}</p>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Dialog */}
      <ExpenseDialog
        open={showDialog}
        onOpenChange={setShowDialog}
        expense={selectedExpense}
        onSave={handleSave}
      />
    </div>
  )
}