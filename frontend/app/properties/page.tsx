import { DashboardLayout } from "@/components/dashboard-layout"
import { PropertiesView } from "@/components/properties/properties-view"
import { ProtectedRoute } from "@/components/auth/protected-route"

export default function PropertiesPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <PropertiesView />
      </DashboardLayout>
    </ProtectedRoute>
  )
}
