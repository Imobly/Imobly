"use client"

import { useState, useEffect } from "react"
import { Badge } from "@/components/ui/badge"
import { RefreshCw } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { usePayments } from "@/lib/hooks/usePayments"
import { apiClient } from "@/lib/api/client"
import { currencyFormat } from "@/lib/utils"

interface RecentPaymentsProps {
  period?: string
}

const statusConfig = {
  paid: { label: "Pago", className: "bg-green-100 text-green-800" },
  pending: { label: "Pendente", className: "bg-yellow-100 text-yellow-800" },
  partial: { label: "Parcial", className: "bg-orange-100 text-orange-800" },
  overdue: { label: "Atrasado", className: "bg-red-100 text-red-800" },
}

interface EnrichedPayment {
  id: number
  total_amount: number
  status: string
  tenant_name: string
  property_address: string
}

export function RecentPayments({ period = "6months" }: RecentPaymentsProps) {
  const { payments, loading: paymentsLoading } = usePayments()
  const [enrichedPayments, setEnrichedPayments] = useState<EnrichedPayment[]>([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    const enrichPayments = async () => {
      if (paymentsLoading) return
      
      try {
        // Pegar apenas os 2 últimos pagamentos ordenados por data de criação
        const recentPayments = [...payments]
          .sort((a, b) => new Date(b.created_at || '').getTime() - new Date(a.created_at || '').getTime())
          .slice(0, 2)
        
        // Buscar informações de inquilino e propriedade
        const enriched = await Promise.all(
          recentPayments.map(async (payment) => {
            let tenant_name = 'Inquilino desconhecido'
            let property_address = 'Endereço não disponível'
            
            try {
              // Buscar inquilino
              if (payment.tenant_id) {
                const tenant = await apiClient.get<{ name: string }>(`/tenants/${payment.tenant_id}/`)
                if (tenant?.name) tenant_name = tenant.name
              }
            } catch (e) {
              console.error('Erro ao buscar inquilino:', e)
            }
            
            try {
              // Buscar propriedade
              if (payment.property_id) {
                const property = await apiClient.get<{ address: string }>(`/properties/${payment.property_id}/`)
                if (property?.address) property_address = property.address
              }
            } catch (e) {
              console.error('Erro ao buscar propriedade:', e)
            }
            
            return {
              id: payment.id,
              total_amount: payment.total_amount,
              status: payment.status,
              tenant_name,
              property_address
            }
          })
        )
        
        setEnrichedPayments(enriched)
      } catch (err) {
        console.error('Erro ao enriquecer pagamentos:', err)
      } finally {
        setLoading(false)
      }
    }
    
    enrichPayments()
  }, [payments, paymentsLoading])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[200px]">
        <RefreshCw className="h-5 w-5 animate-spin text-gray-400" />
        <span className="ml-2 text-sm text-gray-600">Carregando...</span>
      </div>
    )
  }

  if (enrichedPayments.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[200px] text-gray-500">
        <p className="text-sm">Nenhum pagamento recente</p>
      </div>
    )
  }

  const getInitials = (name?: string) => {
    if (!name) return "?"
    const parts = name.trim().split(/\s+/)
    if (parts.length === 1) return parts[0].charAt(0).toUpperCase()
    return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase()
  }

  return (
    <div className="space-y-2">
      {enrichedPayments.map((payment) => {
        const initials = getInitials(payment.tenant_name)
        return (
          <div key={payment.id} className="flex items-center justify-between py-2 border-b last:border-0">
            <div className="flex items-start gap-3 min-w-0">
              <Avatar className="h-9 w-9 text-xs font-semibold bg-muted">
                <AvatarFallback>{initials}</AvatarFallback>
              </Avatar>
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">{payment.tenant_name}</p>
                <p className="text-xs text-muted-foreground truncate">{payment.property_address}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 pl-3">
              <p className="text-sm font-semibold whitespace-nowrap">{currencyFormat(payment.total_amount || 0)}</p>
              <Badge
                variant="secondary"
                className={statusConfig[payment.status as keyof typeof statusConfig]?.className || "bg-gray-100 text-gray-800"}
              >
                {statusConfig[payment.status as keyof typeof statusConfig]?.label || payment.status}
              </Badge>
            </div>
          </div>
        )
      })}
    </div>
  )
}
