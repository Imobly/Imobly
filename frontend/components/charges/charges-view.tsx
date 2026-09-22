"use client"

import { useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  AlertTriangle,
  CalendarPlus,
  FileText,
  Search,
  Wallet,
} from "lucide-react"
import { toast } from "sonner"
import { useAging, useCharges } from "@/lib/hooks/useCharges"
import { type Charge, type ChargeStatus, formatBRL } from "@/lib/types/charge"
import { ChargeStatusBadge, ReceiptDialog } from "@/components/charges/receipt-dialog"
import { formatDate } from '@/lib/utils/format'

const FILTROS: { value: string; label: string }[] = [
  { value: "todas", label: "Todas" },
  { value: "em_aberto", label: "Em aberto" },
  { value: "vencida", label: "Vencidas" },
  { value: "parcial", label: "Parciais" },
  { value: "quitada", label: "Quitadas" },
]

const CORES_AGING: Record<string, string> = {
  a_vencer: "text-blue-600",
  d1_30: "text-amber-600",
  d31_60: "text-orange-600",
  d61_90: "text-red-600",
  d90_mais: "text-red-800",
}

export function ChargesView() {
  const [filtro, setFiltro] = useState<string>("em_aberto")
  const [busca, setBusca] = useState("")
  const [selecionada, setSelecionada] = useState<Charge | null>(null)
  const [dialogAberto, setDialogAberto] = useState(false)

  // Filtro de status resolvido no SERVIDOR quando é um status único; "em
  // aberto" é um conjunto (aberta + parcial + vencida) e tem parâmetro próprio.
  const filtros = useMemo(() => {
    if (filtro === "em_aberto") return { only_open: true, limit: 300 }
    if (filtro === "todas") return { limit: 300 }
    return { status: filtro as ChargeStatus, limit: 300 }
  }, [filtro])

  const { charges, loading, error, addEntry, settle, generate } = useCharges(filtros)
  const { aging } = useAging()

  const visiveis = useMemo(() => {
    const termo = busca.trim().toLowerCase()
    if (!termo) return charges
    return charges.filter(
      (c) =>
        (c.tenant_name || "").toLowerCase().includes(termo) ||
        (c.property_name || "").toLowerCase().includes(termo)
    )
  }, [charges, busca])

  const totais = useMemo(() => {
    const emAberto = charges.filter((c) => c.position.balance > 0)
    return {
      saldo: emAberto.reduce((s, c) => s + c.position.balance, 0),
      vencidas: emAberto.filter((c) => c.position.days_overdue > 0).length,
      parciais: charges.filter((c) => c.status === "parcial").length,
    }
  }, [charges])

  const gerarMes = async () => {
    const criadas = await generate()
    if (criadas === null) {
      toast.error("Não foi possível gerar as cobranças")
      return
    }
    toast.success(
      criadas > 0
        ? `${criadas} cobrança(s) emitida(s) para este mês.`
        : "As cobranças deste mês já estavam emitidas."
    )
  }

  const abrirRecebimento = (charge: Charge) => {
    setSelecionada(charge)
    setDialogAberto(true)
  }

  if (error) {
    return (
      <EmptyState
        icon={AlertTriangle}
        variant="error"
        title="Erro ao carregar cobranças"
        description={error}
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* ── Resumo ── */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Saldo em aberto
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatBRL(totais.saldo)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              já com multa e juros de hoje
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Cobranças vencidas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{totais.vencidas}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {totais.parciais} com pagamento parcial
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Vencidos por faixa
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            {aging ? (
              aging.buckets
                .filter((b) => b.bucket !== "a_vencer" && b.amount > 0)
                .map((b) => (
                  <div key={b.bucket} className="flex justify-between text-sm">
                    <span className="text-muted-foreground">{b.label}</span>
                    <span className={CORES_AGING[b.bucket]}>{formatBRL(b.amount)}</span>
                  </div>
                ))
            ) : (
              <span className="text-sm text-muted-foreground">—</span>
            )}
            {aging && aging.total_overdue === 0 && (
              <span className="text-sm text-green-700">Nada vencido.</span>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Ações e filtros ── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 gap-2">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar por inquilino ou imóvel"
              className="pl-8"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
            />
          </div>
          <Select value={filtro} onValueChange={setFiltro}>
            <SelectTrigger className="w-[160px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {FILTROS.map((f) => (
                <SelectItem key={f.value} value={f.value}>
                  {f.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button onClick={gerarMes} variant="outline">
          <CalendarPlus className="mr-2 h-4 w-4" />
          Gerar cobranças do mês
        </Button>
      </div>

      {/* ── Lista ── */}
      {loading ? (
        <div className="flex items-center justify-center h-40 text-muted-foreground">
          Carregando cobranças...
        </div>
      ) : visiveis.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="Nenhuma cobrança"
          description={
            filtro === "em_aberto"
              ? "Nada em aberto neste filtro. Use “Gerar cobranças do mês” para emitir as parcelas dos contratos ativos."
              : "Nenhuma cobrança encontrada para este filtro."
          }
          action={{ label: "Gerar cobranças do mês", onClick: gerarMes }}
        />
      ) : (
        <div className="space-y-2">
          {visiveis.map((charge) => (
            <ChargeRow key={charge.id} charge={charge} onReceber={abrirRecebimento} />
          ))}
        </div>
      )}

      <ReceiptDialog
        charge={selecionada}
        open={dialogAberto}
        onOpenChange={setDialogAberto}
        onSubmit={(valor, data, metodo) =>
          addEntry(selecionada!.id, { date: data, amount: valor, method: metodo })
        }
        onSettle={(data, metodo) => settle(selecionada!.id, data, metodo)}
      />
    </div>
  )
}

function ChargeRow({
  charge,
  onReceber,
}: {
  charge: Charge
  onReceber: (charge: Charge) => void
}) {
  const { position } = charge
  const competencia = formatDate(charge.competencia, {
    month: "2-digit",
    year: "numeric",
  })

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium truncate">
              {charge.tenant_name || `Inquilino #${charge.tenant_id}`}
            </span>
            <ChargeStatusBadge charge={charge} />
            {position.days_overdue > 0 && position.balance > 0 && (
              <Badge variant="secondary" className="bg-red-100 text-red-800">
                <AlertTriangle className="mr-1 h-3 w-3" />
                {position.days_overdue} dias
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground truncate">
            {charge.property_name || `Imóvel #${charge.property_id}`} · competência {competencia} ·
            vence em {formatDate(charge.due_date)}
          </p>
        </div>

        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-xs text-muted-foreground">Devido</div>
            <div className="text-sm">{formatBRL(position.total_due)}</div>
          </div>
          {position.paid_amount > 0 && (
            <div className="text-right">
              <div className="text-xs text-muted-foreground">Recebido</div>
              <div className="text-sm text-green-700">{formatBRL(position.paid_amount)}</div>
            </div>
          )}
          <div className="text-right">
            {/* O saldo é o número que importa: é o que ainda se cobra. O painel
                antigo mostrava aqui o valor PAGO nos registros parciais. */}
            <div className="text-xs text-muted-foreground">Saldo</div>
            <div
              className={`font-bold ${position.balance > 0 ? "text-red-600" : "text-green-700"}`}
            >
              {formatBRL(position.balance)}
            </div>
          </div>
          {position.balance > 0 && (
            <Button size="sm" onClick={() => onReceber(charge)}>
              <Wallet className="mr-2 h-4 w-4" />
              Receber
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
