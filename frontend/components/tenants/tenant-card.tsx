"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { StatusDot, type StatusTone } from "@/components/ui/status-dot"
import { Phone, Building2, Edit, Trash2, Calendar } from "lucide-react"
import { TenantResponse } from "@/lib/types/api"
import { TenantDetailDialog } from "@/components/tenants/tenant-detail-dialog"
import { formatCurrency } from '@/lib/utils/format'

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

const statusConfig: Record<string, { label: string; tone: StatusTone }> = {
  ativo: { label: "Ativo", tone: "brand" },
  inativo: { label: "Inativo", tone: "neutral" },
}

// Situação financeira ao lado do status do contrato: são perguntas
// diferentes. Um inquilino "Ativo" pode dever três meses, e era exatamente
// isso que o card não mostrava.
const situacaoConfig: Record<string, { label: string; tone: StatusTone }> = {
  em_dia: { label: "Em dia", tone: "positive" },
  atraso_leve: { label: "Atraso leve", tone: "warning" },
  inadimplente: { label: "Inadimplente", tone: "critical" },
  critico: { label: "Crítico", tone: "critical" },
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

  const status = statusConfig[tenant.status as keyof typeof statusConfig] ?? statusConfig.inativo
  const situacao = tenant.situacao_financeira
    ? situacaoConfig[tenant.situacao_financeira]
    : undefined

  // Sem contrato, o card dizia três vezes a mesma coisa em itálico cinza
  // ("Sem imóvel vinculado", "Sem contrato ativo", "Sem valor definido").
  // É um estado só, e o que falta ali é a ação de vincular.
  const semContrato = !tenant.property_name && !tenant.due_day && !tenant.rent

  return (
    <>
      <Card
        className="group hover:border-brand-300 cursor-pointer gap-0 py-0 shadow-none transition-colors hover:shadow-md"
        onClick={() => setShowDetailDialog(true)}
      >
        <CardContent className="relative p-5">
          {/* Ações: só no hover, e excluir sem vermelho cheio. */}
          <div className="absolute top-4 right-4 z-10 flex gap-2 opacity-0 transition-opacity group-focus-within:opacity-100 group-hover:opacity-100">
            <Button
              variant="outline"
              size="icon"
              className="size-9 bg-white"
              aria-label={`Editar ${tenant.name}`}
              onClick={(e) => {
                e.stopPropagation()
                onEdit(tenant)
              }}
            >
              <Edit className="h-4 w-4" />
            </Button>
            {onDelete && (
              <Button
                variant="outline"
                size="icon"
                className="text-critical-strong border-critical-soft hover:bg-critical-soft size-9 bg-white"
                aria-label={`Excluir ${tenant.name}`}
                onClick={(e) => {
                  e.stopPropagation()
                  onDelete(tenant.id)
                }}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>

          {/* Header: iniciais + nome + estados */}
          <div className="flex items-center gap-3.5 pr-20">
            <span className="bg-brand-50 text-brand-700 flex size-12 shrink-0 items-center justify-center rounded-xl text-sm font-bold">
              {getInitials(tenant.name)}
            </span>
            <div className="min-w-0">
              <h3 className="truncate leading-tight font-bold">{tenant.name}</h3>
              <div className="mt-1.5 flex flex-wrap items-center gap-2">
                <StatusDot tone={status.tone}>{status.label}</StatusDot>
                {situacao && tenant.situacao_financeira !== "em_dia" && (
                  <StatusDot tone={situacao.tone} emphasis>
                    {situacao.label}
                    {tenant.dias_atraso ? ` · ${tenant.dias_atraso}d` : ""}
                  </StatusDot>
                )}
              </div>
            </div>
          </div>

          <div className="bg-hairline my-4 h-px" />

          <div className="flex flex-col gap-2.5 text-sm">
            <p className="text-foreground/80 flex items-center gap-2.5">
              <Phone className="text-muted-foreground h-4 w-4 shrink-0" />
              {formatPhone(tenant.phone)}
            </p>

            {semContrato ? (
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-muted-foreground flex items-center gap-2.5">
                  <Building2 className="h-4 w-4 shrink-0" />
                  Sem contrato ativo
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="border-brand-100 text-brand-700"
                  onClick={(e) => {
                    e.stopPropagation()
                    onEdit(tenant)
                  }}
                >
                  Vincular imóvel
                </Button>
              </div>
            ) : (
              <>
                {tenant.property_name && (
                  <p className="text-foreground/80 flex items-center gap-2.5">
                    <Building2 className="text-muted-foreground h-4 w-4 shrink-0" />
                    <span className="min-w-0">
                      <span className="block truncate font-medium">{tenant.property_name}</span>
                      {tenant.property_address && (
                        <span className="text-muted-foreground block truncate text-xs">
                          {tenant.property_address}
                        </span>
                      )}
                    </span>
                  </p>
                )}

                {tenant.due_day && (
                  <p className="text-foreground/80 flex items-center gap-2.5">
                    <Calendar className="text-muted-foreground h-4 w-4 shrink-0" />
                    Vence todo dia <span className="font-medium">{tenant.due_day}</span>
                  </p>
                )}

                {tenant.rent && tenant.rent > 0 && (
                  <>
                    <div className="bg-hairline mt-1 h-px" />
                    <div className="flex items-end justify-between">
                      <span className="text-muted-foreground text-xs">Aluguel</span>
                      <span className="font-display text-xl font-bold tracking-tight">
                        {formatCurrency(tenant.rent)}
                      </span>
                    </div>
                  </>
                )}
              </>
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
