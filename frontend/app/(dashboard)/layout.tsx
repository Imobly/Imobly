import type React from "react"
import { ProtectedRoute } from "@/components/auth/protected-route"
import { DashboardLayout } from "@/components/dashboard-layout"

// Layout do route group `(dashboard)`: o Next.js App Router mantém este
// componente montado entre navegações dentro do grupo — sidebar, header e
// o contexto de auth não são recriados a cada troca de rota, só o
// conteúdo da página muda.
export default function DashboardGroupLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ProtectedRoute>
      <DashboardLayout>{children}</DashboardLayout>
    </ProtectedRoute>
  )
}
