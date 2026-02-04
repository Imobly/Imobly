import { DashboardLayout } from "@/components/dashboard-layout"
import { PaymentsView } from "@/components/payments/payments-view"
import { ProtectedRoute } from "@/components/auth/protected-route"

export default function PaymentsPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <PaymentsView />
      </DashboardLayout>
    </ProtectedRoute>
  )
}
