import { DashboardLayout } from "@/components/dashboard-layout"
import { StatusView } from "@/components/status/status-view"
import { ProtectedRoute } from "@/components/auth/protected-route"

export default function StatusPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-foreground">Status Geral</h1>
          <p className="text-muted-foreground mt-2">Visão geral do status de todos os sistemas e operações</p>
        </div>
        <StatusView />
      </DashboardLayout>
    </ProtectedRoute>
  )
}
