"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Phone, Building2, Edit, Trash2, Calendar, DollarSign } from "lucide-react"
import { TenantResponse } from "@/lib/types/api"
import { TenantDetailDialog } from "@/components/tenants/tenant-detail-dialog"

interface TenantCardProps {
  tenant: TenantResponse & {
    property_name?: string
    property_address?: string
    rent?: number
    due_day?: number
  }
  onEdit: (tenant: any) => void
  onDelete?: (tenantId: number) => void
}

const statusConfig = {
  active: { label: "Ativo", className: "bg-green-100 text-green-800" },
  inactive: { label: "Inativo", className: "bg-gray-100 text-gray-800" },
}

export function TenantCard({ tenant, onEdit, onDelete }: TenantCardProps) {
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  
  const getInitials = (name: string) => {
    return name
      .split(" ")
      .filter(n => n.length > 0)
      .slice(0, 2)
      .map((n) => n[0])
      .join("")
      .toUpperCase()
  }

  const formatPhone = (phone: string) => {
    // Formatar telefone brasileiro (XX) XXXXX-XXXX
    const cleaned = phone.replace(/\D/g, '')
    if (cleaned.length === 11) {
      return `(${cleaned.slice(0, 2)}) ${cleaned.slice(2, 7)}-${cleaned.slice(7)}`
    } else if (cleaned.length === 10) {
      return `(${cleaned.slice(0, 2)}) ${cleaned.slice(2, 6)}-${cleaned.slice(6)}`
    }
    return phone
  }

  return (
    <>
      <Card 
        className="hover:shadow-lg transition-all cursor-pointer hover:border-blue-300 group"
        onClick={() => setShowDetailDialog(true)}
      >
        <CardContent className="p-6 relative">
          {/* Botões de ação - estilo igual ao PropertyCard */}
          <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
            <Button 
              variant="secondary" 
              size="sm" 
              className="h-8 w-8 p-0"
              onClick={(e) => {
                e.stopPropagation()
                onEdit(tenant)
              }}
            >
              <Edit className="h-4 w-4" />
            </Button>
            {onDelete && (
              <Button 
                variant="destructive" 
                size="sm" 
                className="h-8 w-8 p-0"
                onClick={(e) => {
                  e.stopPropagation()
                  onDelete(tenant.id)
                }}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>

          {/* Header: Avatar + Nome + Status */}
          <div className="flex items-start justify-between mb-4 pr-20">
            <div className="flex items-center space-x-3">
              <Avatar className="h-14 w-14 ring-2 ring-blue-100">
                <AvatarFallback className="bg-gradient-to-br from-blue-500 to-blue-600 text-white font-semibold text-lg">
                  {getInitials(tenant.name)}
                </AvatarFallback>
              </Avatar>
              <div>
                <h3 className="font-semibold text-lg leading-tight">{tenant.name}</h3>
                <Badge 
                  variant="secondary" 
                  className={`mt-1 ${statusConfig[tenant.status as keyof typeof statusConfig].className}`}
                >
                  {statusConfig[tenant.status as keyof typeof statusConfig].label}
                </Badge>
              </div>
            </div>
          </div>

          {/* Informações Principais */}
          <div className="space-y-3">
            {/* Telefone */}
            <div className="flex items-center text-sm">
              <Phone className="mr-3 h-4 w-4 text-blue-600" />
              <span className="font-medium text-gray-700">{formatPhone(tenant.phone)}</span>
            </div>

            {/* Imóvel */}
            {tenant.property_name ? (
              <div className="flex items-center text-sm">
                <Building2 className="mr-3 h-4 w-4 text-blue-600" />
                <div className="flex-1 min-w-0">
                  <span className="font-medium text-gray-700 block truncate">{tenant.property_name}</span>
                  {tenant.property_address && (
                    <span className="text-xs text-gray-500 block truncate">{tenant.property_address}</span>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex items-center text-sm">
                <Building2 className="mr-3 h-4 w-4 text-gray-400" />
                <span className="text-gray-400 italic">Sem imóvel vinculado</span>
              </div>
            )}

            {/* Data de Vencimento */}
            {tenant.due_day ? (
              <div className="flex items-center text-sm">
                <Calendar className="mr-3 h-4 w-4 text-blue-600" />
                <span className="text-gray-700">Vencimento: <span className="font-medium">Todo dia {tenant.due_day}</span></span>
              </div>
            ) : (
              <div className="flex items-center text-sm">
                <Calendar className="mr-3 h-4 w-4 text-gray-400" />
                <span className="text-gray-400 italic">Sem contrato ativo</span>
              </div>
            )}

            {/* Valor do Aluguel */}
            {tenant.rent && tenant.rent > 0 ? (
              <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                <div className="flex items-center text-sm">
                  <DollarSign className="mr-2 h-4 w-4 text-green-600" />
                  <span className="text-gray-600">Aluguel</span>
                </div>
                <span className="text-lg font-bold text-green-700">
                  R$ {tenant.rent.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
            ) : (
              <div className="flex items-center text-sm pt-2 border-t border-gray-100">
                <DollarSign className="mr-3 h-4 w-4 text-gray-400" />
                <span className="text-gray-400 italic">Sem valor definido</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Dialog de Detalhes */}
      <TenantDetailDialog
        tenant={tenant}
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        onEdit={() => { setShowDetailDialog(false); onEdit(tenant); }}
        onDelete={onDelete ? () => { setShowDetailDialog(false); onDelete(tenant.id); } : undefined}
      />
    </>
  )
}
