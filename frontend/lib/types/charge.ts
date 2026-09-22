/**
 * Cobranças e recebimentos.
 *
 * Uma COBRANÇA é o que o inquilino deve num mês; um RECEBIMENTO é cada valor
 * que entra. O modelo antigo tinha só "pagamento", e por isso não conseguia
 * representar um aluguel de R$ 1.000 pago em duas parcelas de 600 e 400.
 *
 * `position` é a parte que a tela consome: vem calculada do servidor, com
 * multa e juros do dia. Não recalcule nada disso no cliente — o arredondamento
 * diverge do backend já no primeiro centavo.
 */

import { formatCurrency } from '@/lib/utils/format'

export type ChargeStatus = 'aberta' | 'parcial' | 'vencida' | 'quitada' | 'cancelada'

export type AgingBucketKey = 'a_vencer' | 'd1_30' | 'd31_60' | 'd61_90' | 'd90_mais'

export type SituacaoFinanceira = 'em_dia' | 'atraso_leve' | 'inadimplente' | 'critico'

export interface ChargePosition {
  base_amount: number
  fine_amount: number
  interest_amount: number
  /** Aluguel + encargos + multa + juros na data de referência. */
  total_due: number
  /** Soma dos recebimentos. */
  paid_amount: number
  /** O que ainda falta. Zero quando quitada. */
  balance: number
  days_overdue: number
  aging_bucket: AgingBucketKey
  reference_date: string
  settled_at: string | null
}

export interface PaymentEntry {
  id: number
  charge_id: number
  date: string
  amount: number
  method: string | null
  description: string | null
  created_at: string
}

export interface Charge {
  id: number
  user_id: number
  contract_id: number
  property_id: number
  tenant_id: number
  /** Primeiro dia do mês a que o aluguel se refere. */
  competencia: string
  due_date: string
  rent_amount: number
  charges_amount: number
  discount_amount: number
  fine_rate: number
  interest_rate: number
  status: ChargeStatus
  description: string | null
  canceled_at: string | null
  created_at: string
  updated_at: string
  position: ChargePosition
  tenant_name?: string | null
  property_name?: string | null
}

export interface ChargeDetail extends Charge {
  entries: PaymentEntry[]
}

export interface ChargeFilters {
  skip?: number
  limit?: number
  status?: ChargeStatus
  property_id?: number
  tenant_id?: number
  contract_id?: number
  competencia?: string
  due_from?: string
  due_to?: string
  only_open?: boolean
}

export interface PaymentEntryInput {
  date: string
  amount: number
  method?: string
  description?: string
}

export interface GenerateChargesResult {
  competencia: string
  created: number
  skipped_existing: number
  /** Contratos sem `due_day`: sem dia de vencimento não há como cobrar multa. */
  skipped_no_due_day: number
  charge_ids: number[]
}

export interface AgingBucket {
  bucket: AgingBucketKey
  label: string
  count: number
  amount: number
}

export interface AgingReport {
  as_of: string
  buckets: AgingBucket[]
  total_open: number
  total_overdue: number
}

/** Uma linha por inquilino em débito, ordenada do pior atraso ao menor. */
export interface DelinquencyRow {
  tenant_id: number
  tenant_name: string
  property_id: number
  property_name: string
  balance: number
  overdue_balance: number
  open_charges: number
  oldest_due_date: string
  days_overdue: number
  situacao: SituacaoFinanceira
}

export interface TenantLedgerEntry {
  charge_id: number
  competencia: string
  due_date: string
  property_id: number
  property_name: string | null
  status: ChargeStatus
  position: ChargePosition
}

export interface TenantLedger {
  tenant_id: number
  tenant_name: string
  as_of: string
  situacao: SituacaoFinanceira
  open_balance: number
  overdue_balance: number
  oldest_overdue_days: number
  open_charges: number
  charges_settled: number
  settled_on_time: number
  /** % de cobranças quitadas em dia — o que pesa na renovação do contrato. */
  on_time_rate: number
  average_delay_days: number
  entries: TenantLedgerEntry[]
}

export const SITUACAO_LABEL: Record<SituacaoFinanceira, string> = {
  em_dia: 'Em dia',
  atraso_leve: 'Atraso leve',
  inadimplente: 'Inadimplente',
  critico: 'Crítico',
}

export const CHARGE_STATUS_LABEL: Record<ChargeStatus, string> = {
  aberta: 'Em aberto',
  parcial: 'Parcial',
  vencida: 'Vencida',
  quitada: 'Quitada',
  cancelada: 'Cancelada',
}

export const formatBRL = (valor: number): string =>
  formatCurrency(valor || 0)
