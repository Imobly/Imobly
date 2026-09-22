"use client"

import { useMemo, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { EmptyState } from "@/components/ui/empty-state"
import { AgingRuler, type AgingTone } from "@/components/ui/aging-ruler"
import { StatusDot } from "@/components/ui/status-dot"
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

const TOM_AGING: Record<string, AgingTone> = {
  a_vencer: "info",
  d1_30: "warning",
  d31_60: "warning",
  d61_90: "critical",
  d90_mais: "critical",
}

/** Ordem da régua — a API pode devolver os buckets em qualquer ordem. */
const ORDEM_AGING = ["d1_30", "d31_60", "d61_90", "d90_mais"]

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

  // A régua precisa das quatro faixas sempre, inclusive as zeradas: saber que
  // não há nada entre 0 e 30 dias é informação, não ausência de informação.
  const colunasAging = useMemo(() => {
    const porBucket = new Map(
      (aging?.buckets ?? []).map((b) => [b.bucket, b])
    )
    const rotulosPadrao: Record<string, string> = {
      d1_30: "1–30 dias",
      d31_60: "31–60 dias",
      d61_90: "61–90 dias",
      d90_mais: "Mais de 90 dias",
    }
    return ORDEM_AGING.map((bucket) => {
      const b = porBucket.get(bucket as never)
      const amount = b?.amount ?? 0
      return {
        label: b?.label ?? rotulosPadrao[bucket],
        amount,
        formatted: formatBRL(amount),
        tone: TOM_AGING[bucket],
      }
    })
  }, [aging])

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
      {/* ── Resumo: saldo em destaque + régua de atraso ── */}
      <AgingRuler
        headlineLabel="Saldo em aberto"
        headline={formatBRL(totais.saldo)}
        headlineTone={totais.saldo > 0 ? "critical" : "positive"}
        badge={
          totais.vencidas > 0 ? (
            <StatusDot tone="critical" emphasis>
              {totais.vencidas} {totais.vencidas === 1 ? "vencida" : "vencidas"}
            </StatusDot>
          ) : (
            <StatusDot tone="positive" emphasis>
              Nada vencido
            </StatusDot>
          )
        }
        caption={
          totais.parciais > 0
            ? `${totais.parciais} com pagamento parcial · já com multa e juros de hoje`
            : "já com multa e juros de hoje"
        }
        columns={colunasAging}
      />

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
        <div className="space-y-3">
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

  // Quanto do devido já entrou. Três números soltos (devido / recebido /
  // saldo) obrigam o olho a fazer a conta; a barra faz por ele.
  const proporcao =
    position.total_due > 0
      ? Math.min(100, (position.paid_amount / position.total_due) * 100)
      : 0

  return (
    <article className="bg-card border-border hover:border-brand-300 rounded-2xl border p-4 transition-colors sm:p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:gap-6">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="truncate font-semibold">
              {charge.tenant_name || `Inquilino #${charge.tenant_id}`}
            </h3>
            <ChargeStatusBadge charge={charge} />
            {position.days_overdue > 0 && position.balance > 0 && (
              <StatusDot tone="critical" emphasis>
                {position.days_overdue} dias
              </StatusDot>
            )}
          </div>
          <p className="text-muted-foreground mt-1 truncate text-sm">
            {charge.property_name || `Imóvel #${charge.property_id}`} · competência {competencia} ·
            vence em {formatDate(charge.due_date)}
          </p>
        </div>

        <div className="lg:w-72 lg:shrink-0">
          <div className="text-muted-foreground mb-1.5 flex justify-between text-xs">
            <span>
              Recebido{" "}
              <strong className="text-positive font-bold">
                {formatBRL(position.paid_amount)}
              </strong>
            </span>
            <span>de {formatBRL(position.total_due)}</span>
          </div>
          <div className="bg-muted h-2 overflow-hidden rounded-full">
            <div
              className="bg-positive h-full rounded-full"
              style={{ width: `${proporcao}%` }}
            />
          </div>
        </div>

        <div className="lg:w-32 lg:shrink-0 lg:text-right">
          {/* O saldo é o número que importa: é o que ainda se cobra. O painel
              antigo mostrava aqui o valor PAGO nos registros parciais. */}
          <div className="text-muted-foreground text-xs">Saldo</div>
          <div
            className={`text-lg font-bold ${
              position.balance > 0 ? "text-critical" : "text-positive"
            }`}
          >
            {formatBRL(position.balance)}
          </div>
        </div>

        {position.balance > 0 && (
          <Button className="lg:shrink-0" onClick={() => onReceber(charge)}>
            <Wallet className="mr-2 h-4 w-4" />
            Receber
          </Button>
        )}
      </div>
    </article>
  )
}
