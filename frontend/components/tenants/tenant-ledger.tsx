"use client"

import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { AlertTriangle, Wallet } from "lucide-react"
import { useTenantLedger } from "@/lib/hooks/useCharges"
import { SITUACAO_LABEL, formatBRL, type SituacaoFinanceira } from "@/lib/types/charge"
import { formatDate } from '@/lib/utils/format'

const CORES_SITUACAO: Record<SituacaoFinanceira, string> = {
  em_dia: "bg-green-100 text-green-800",
  atraso_leve: "bg-amber-100 text-amber-800",
  inadimplente: "bg-orange-100 text-orange-900",
  critico: "bg-red-100 text-red-800",
}

const CORES_STATUS: Record<string, string> = {
  aberta: "bg-blue-100 text-blue-800",
  parcial: "bg-orange-100 text-orange-800",
  vencida: "bg-red-100 text-red-800",
  quitada: "bg-green-100 text-green-800",
  cancelada: "bg-gray-100 text-gray-800",
}

/**
 * Extrato financeiro do inquilino.
 *
 * Reúne as três perguntas que se faz antes de cobrar ou de renovar: quanto ele
 * deve hoje, há quanto tempo, e como foi o histórico dele. A última é a que
 * decide renovação e não existia em lugar nenhum do sistema.
 */
export function TenantLedgerPanel({ tenantId }: { tenantId: number }) {
  const { ledger, loading, error } = useTenantLedger(tenantId)

  if (loading) {
    return <p className="text-sm text-muted-foreground">Carregando extrato...</p>
  }
  if (error || !ledger) {
    return <p className="text-sm text-red-600">Não foi possível carregar o extrato.</p>
  }

  const temDivida = ledger.open_balance > 0

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary" className={CORES_SITUACAO[ledger.situacao]}>
          {SITUACAO_LABEL[ledger.situacao]}
        </Badge>
        {ledger.oldest_overdue_days > 0 && (
          <Badge variant="secondary" className="bg-red-100 text-red-800">
            <AlertTriangle className="mr-1 h-3 w-3" />
            atraso mais antigo: {ledger.oldest_overdue_days} dias
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Indicador
          rotulo="Saldo devedor"
          valor={formatBRL(ledger.open_balance)}
          destaque={temDivida ? "text-red-600" : "text-green-700"}
          nota="com multa e juros de hoje"
        />
        <Indicador
          rotulo="Cobranças em aberto"
          valor={String(ledger.open_charges)}
          nota={ledger.overdue_balance > 0 ? `${formatBRL(ledger.overdue_balance)} vencido` : "nada vencido"}
        />
        <Indicador
          rotulo="Pagou em dia"
          valor={`${ledger.on_time_rate.toFixed(0)}%`}
          nota={`${ledger.settled_on_time} de ${ledger.charges_settled} quitadas`}
        />
        <Indicador
          rotulo="Atraso médio"
          valor={`${ledger.average_delay_days.toFixed(1)} d`}
          nota="nas cobranças já quitadas"
        />
      </div>

      <Separator />

      <div>
        <h4 className="font-medium text-sm mb-2 flex items-center">
          <Wallet className="h-4 w-4 mr-2 text-blue-600" />
          Histórico de cobranças
        </h4>
        {ledger.entries.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Nenhuma cobrança emitida para este inquilino ainda.
          </p>
        ) : (
          <div className="space-y-1">
            {ledger.entries.map((item) => (
              <div
                key={item.charge_id}
                className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">
                      {formatDate(item.competencia, {
                        month: "2-digit",
                        year: "numeric",
                      })}
                    </span>
                    <Badge variant="secondary" className={CORES_STATUS[item.status]}>
                      {item.status}
                    </Badge>
                    {item.position.days_overdue > 0 && item.position.balance > 0 && (
                      <span className="text-xs text-red-600">
                        {item.position.days_overdue} dias
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground truncate">
                    {item.property_name || `Imóvel #${item.property_id}`} · vence{" "}
                    {formatDate(item.due_date)}
                  </span>
                </div>
                <div className="text-right shrink-0 pl-3">
                  <div className="text-xs text-muted-foreground">
                    recebido {formatBRL(item.position.paid_amount)}
                  </div>
                  <div
                    className={
                      item.position.balance > 0
                        ? "font-semibold text-red-600"
                        : "font-semibold text-green-700"
                    }
                  >
                    {item.position.balance > 0
                      ? `saldo ${formatBRL(item.position.balance)}`
                      : "quitada"}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function Indicador({
  rotulo,
  valor,
  nota,
  destaque,
}: {
  rotulo: string
  valor: string
  nota?: string
  destaque?: string
}) {
  return (
    <div className="rounded-lg border p-3">
      <div className="text-xs text-muted-foreground">{rotulo}</div>
      <div className={`text-lg font-bold ${destaque ?? ""}`}>{valor}</div>
      {nota && <div className="text-xs text-muted-foreground mt-0.5">{nota}</div>}
    </div>
  )
}
