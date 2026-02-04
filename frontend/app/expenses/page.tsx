import { DashboardLayout } from "@/components/dashboard-layout"
import { ExpensesView } from "@/components/expenses/expenses-view"
import { ProtectedRoute } from "@/components/auth/protected-route"

export default function ExpensesPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-foreground">Despesas e Manutenção</h1>
          <p className="text-muted-foreground mt-2">Gerencie todas as despesas e manutenções dos seus imóveis</p>
        </div>
        <ExpensesView />
      </DashboardLayout>
    </ProtectedRoute>
  )
}
