import { DashboardLayout } from "@/components/dashboard-layout"
import { TenantsView } from "@/components/tenants/tenants-view"
import { ProtectedRoute } from "@/components/auth/protected-route"

export default function TenantsPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <TenantsView />
      </DashboardLayout>
    </ProtectedRoute>
  )
}
