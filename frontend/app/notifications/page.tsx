import { DashboardLayout } from "@/components/dashboard-layout"
import { NotificationsView } from "@/components/notifications/notifications-view"
import { ProtectedRoute } from "@/components/auth/protected-route"

export default function NotificationsPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-foreground">Notificações</h1>
          <p className="text-muted-foreground mt-2">Acompanhe alertas importantes e status do sistema</p>
        </div>
        <NotificationsView />
      </DashboardLayout>
    </ProtectedRoute>
  )
}
