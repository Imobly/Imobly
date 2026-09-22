"use client"

import { useMemo, useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { AlertTriangle } from "lucide-react"
import { toast } from "sonner"
import { type Charge, formatBRL } from "@/lib/types/charge"
import { toNumber } from "@/lib/utils/format"

interface ReceiptDialogProps {
  charge: Charge | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (valor: number, data: string, metodo?: string) => Promise<boolean>
  onSettle: (data: string, metodo?: string) => Promise<boolean>
}

const METODOS = [
  { value: "pix", label: "PIX" },
  { value: "boleto", label: "Boleto" },
  { value: "transferencia", label: "Transferência" },
  { value: "dinheiro", label: "Dinheiro" },
  { value: "cartao_credito", label: "Cartão de crédito" },
  { value: "cartao_debito", label: "Cartão de débito" },
  { value: "outro", label: "Outro" },
]

/**
 * Registro de recebimento — o caminho para o pagamento parcial.
 *
 * Duas ações distintas de propósito:
 *
 *  • "Quitar saldo" não manda valor nenhum. O servidor lança exatamente o
 *    saldo do dia, com multa e juros calculados lá. Se a tela montasse esse
 *    número, o arredondamento divergiria do backend e a cobrança ficaria com
 *    saldo de centavos que ninguém consegue zerar.
 *
 *  • "Registrar" manda o valor digitado, que pode ser MENOR que o devido — e é
 *    esse o caso comum: aluguel de 1.000, entrou 600. A diferença continua
 *    existindo na mesma cobrança, e não como dívida nova.
 */
export function ReceiptDialog({
  charge,
  open,
  onOpenChange,
  onSubmit,
  onSettle,
}: ReceiptDialogProps) {
  const hoje = new Date().toISOString().slice(0, 10)
  const [valor, setValor] = useState("")
  const [data, setData] = useState(hoje)
  const [metodo, setMetodo] = useState<string>("pix")
  const [salvando, setSalvando] = useState(false)

  const saldo = charge?.position.balance ?? 0
  const valorNumerico = useMemo(() => {
    const n = toNumber(valor)
    return Number.isNaN(n) ? 0 : n
  }, [valor])

  const restante = Math.max(0, saldo - valorNumerico)
  const ficaraParcial = valorNumerico > 0 && valorNumerico < saldo

  const fechar = () => {
    setValor("")
    setData(hoje)
    setMetodo("pix")
    onOpenChange(false)
  }

  const registrar = async () => {
    if (valorNumerico <= 0) {
      toast.error("Informe o valor recebido")
      return
    }
    setSalvando(true)
    const ok = await onSubmit(valorNumerico, data, metodo)
    setSalvando(false)
    if (ok) {
      toast.success(
        ficaraParcial
          ? `Recebimento registrado. Saldo de ${formatBRL(restante)} continua em aberto.`
          : "Recebimento registrado."
      )
      fechar()
    } else {
      toast.error("Não foi possível registrar o recebimento")
    }
  }

  const quitar = async () => {
    setSalvando(true)
    const ok = await onSettle(data, metodo)
    setSalvando(false)
    if (ok) {
      toast.success("Cobrança quitada.")
      fechar()
    } else {
      toast.error("Não foi possível quitar a cobrança")
    }
  }

  if (!charge) return null

  const { position } = charge

  return (
    <Dialog open={open} onOpenChange={(v) => (v ? onOpenChange(v) : fechar())}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Registrar recebimento</DialogTitle>
          <DialogDescription>
            {charge.tenant_name || `Inquilino #${charge.tenant_id}`} —{" "}
            {charge.property_name || `Imóvel #${charge.property_id}`}
          </DialogDescription>
        </DialogHeader>

        <div className="rounded-lg border p-3 space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Aluguel e encargos</span>
            <span>{formatBRL(position.base_amount)}</span>
          </div>
          {position.fine_amount > 0 && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Multa</span>
              <span className="text-red-600">{formatBRL(position.fine_amount)}</span>
            </div>
          )}
          {position.interest_amount > 0 && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Juros ({position.days_overdue} dias)</span>
              <span className="text-red-600">{formatBRL(position.interest_amount)}</span>
            </div>
          )}
          {position.paid_amount > 0 && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Já recebido</span>
              <span className="text-green-700">− {formatBRL(position.paid_amount)}</span>
            </div>
          )}
          <div className="flex justify-between font-semibold pt-1 border-t">
            <span>Saldo devedor hoje</span>
            <span>{formatBRL(saldo)}</span>
          </div>
          {position.days_overdue > 0 && (
            <div className="flex items-center gap-1 pt-1 text-xs text-red-600">
              <AlertTriangle className="h-3 w-3" />
              Vencida há {position.days_overdue} dias — o saldo cresce a cada dia.
            </div>
          )}
        </div>

        <div className="grid gap-3">
          <div className="grid gap-1.5">
            <Label htmlFor="valor">Valor recebido</Label>
            <Input
              id="valor"
              inputMode="decimal"
              placeholder={saldo.toFixed(2)}
              value={valor}
              onChange={(e) => setValor(e.target.value)}
            />
            {ficaraParcial && (
              <p className="text-xs text-orange-600">
                Pagamento parcial: restam {formatBRL(restante)} nesta cobrança.
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="grid gap-1.5">
              <Label htmlFor="data">Data</Label>
              <Input
                id="data"
                type="date"
                value={data}
                onChange={(e) => setData(e.target.value)}
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="metodo">Forma</Label>
              <Select value={metodo} onValueChange={setMetodo}>
                <SelectTrigger id="metodo">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {METODOS.map((m) => (
                    <SelectItem key={m.value} value={m.value}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-2">
          <Button variant="outline" onClick={quitar} disabled={salvando || saldo <= 0}>
            Quitar saldo ({formatBRL(saldo)})
          </Button>
          <Button onClick={registrar} disabled={salvando || valorNumerico <= 0}>
            Registrar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/** Badge de situação da cobrança, com o vocabulário novo. */
export function ChargeStatusBadge({ charge }: { charge: Charge }) {
  const config: Record<string, { label: string; className: string }> = {
    aberta: { label: "Em aberto", className: "bg-blue-100 text-blue-800" },
    parcial: { label: "Parcial", className: "bg-orange-100 text-orange-800" },
    vencida: { label: "Vencida", className: "bg-red-100 text-red-800" },
    quitada: { label: "Quitada", className: "bg-green-100 text-green-800" },
    cancelada: { label: "Cancelada", className: "bg-gray-100 text-gray-800" },
  }
  const item = config[charge.status] ?? config.aberta
  return (
    <Badge variant="secondary" className={item.className}>
      {item.label}
    </Badge>
  )
}
