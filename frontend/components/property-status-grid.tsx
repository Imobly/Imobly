"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Building2, MapPin, User, RefreshCw } from "lucide-react"
import { usePropertiesStatus } from "@/lib/hooks/useDashboard"
import { contractsService } from "@/lib/api/contracts"
import { apiClient } from "@/lib/api/client"
import { currencyFormat } from "@/lib/utils"

interface PropertyStatusGridProps {
  period?: string
}

const statusConfig = {
  occupied: {
    label: "Ocupado",
    className: "bg-green-100 text-green-800",
  },
  vacant: {
    label: "Vago",
    className: "bg-gray-100 text-gray-800",
  },
  maintenance: {
    label: "Manutenção",
    className: "bg-orange-100 text-orange-800",
  },
}

export function PropertyStatusGrid({ period = "6months" }: PropertyStatusGridProps) {
  const { data, loading, error } = usePropertiesStatus(period)
  const [enrichedProperties, setEnrichedProperties] = useState<any[]>([])

  useEffect(() => {
    const enrichProperties = async () => {
      if (!data || !data.properties || data.properties.length === 0) {
        setEnrichedProperties([])
        return
      }

      const enriched = await Promise.all(
        data.properties.map(async (property) => {
          // Somente tenta enriquecer quando ocupada
          if (property.status === 'occupied') {
            try {
              // Preferir busca direta por tenant_id do imóvel se existir
              // @ts-ignore: backend retorna tenant_id no objeto de propriedade
              if ((property as any).tenant_id) {
                try {
                  const tenant = await apiClient.get<{ id: number; name: string }>(`/tenants/${(property as any).tenant_id}/`)
                  if (tenant?.name) return { ...property, tenant_name: tenant.name }
                } catch (_) {}
              }
              const propertyId = property.id || property.property_id
              const contracts = await contractsService.getContracts({ property_id: propertyId, status: 'active' })
              if (Array.isArray(contracts) && contracts.length > 0) {
                const activeContract: any = contracts[0]
                let tenantName = 'Inquilino não identificado'
                if (activeContract.tenant && activeContract.tenant.name) tenantName = activeContract.tenant.name
                if (activeContract.tenant_name) tenantName = activeContract.tenant_name
                return { ...property, tenant_name: tenantName }
              }
            } catch (err) {
              console.error('Erro ao buscar contrato da propriedade:', err)
            }
          }
          return property
        })
      )
      setEnrichedProperties(enriched)
    }

    enrichProperties()
  }, [data])

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-[200px]">
        <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
        <span className="ml-2 text-gray-600">Carregando propriedades...</span>
      </div>
    )
  }

  // Error state
  if (error || !data?.properties) {
    return (
      <div className="flex flex-col items-center justify-center h-[200px] text-gray-500">
        <p className="text-sm">{error || "Nenhuma propriedade encontrada"}</p>
      </div>
    )
  }

  const propertiesToShow = enrichedProperties.length > 0 ? enrichedProperties : (data?.properties || [])

  return (
    <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-4">
      {propertiesToShow.map((property) => (
        <Card key={property.property_id} className="hover:shadow-md transition-shadow max-w-sm">
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center space-x-2">
                <Building2 className="h-3 w-3 text-muted-foreground" />
                <h3 className="font-semibold text-xs">{property.property_name}</h3>
              </div>
              <Badge
                variant="secondary"
                className={`text-[10px] px-1.5 py-0 ${statusConfig[property.status as keyof typeof statusConfig]?.className || ""}`}
              >
                {statusConfig[property.status as keyof typeof statusConfig]?.label || property.status}
              </Badge>
            </div>

            <div className="space-y-1.5 text-xs">
              {property.address && (
                <div className="flex items-center space-x-1 text-muted-foreground">
                  <MapPin className="h-3 w-3" />
                  <span className="truncate">{property.address}</span>
                </div>
              )}

              {property.status === 'occupied' && property.tenant_name && (
                <div className="flex items-center space-x-1 text-muted-foreground">
                  <User className="h-3 w-3" />
                  <span>{property.tenant_name}</span>
                </div>
              )}

              <div className="pt-2 border-t">
                <span className="font-bold text-sm">{currencyFormat(property.expected_monthly_revenue || 0)}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
