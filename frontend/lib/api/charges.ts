import { apiClient, buildQueryString } from './client'
import type {
  AgingReport,
  Charge,
  ChargeDetail,
  ChargeFilters,
  DelinquencyRow,
  GenerateChargesResult,
  PaymentEntry,
  PaymentEntryInput,
  TenantLedger,
} from '@/lib/types/charge'

/**
 * Serviço de cobranças.
 *
 * O backend serializa Decimal como string no JSON; se esses valores chegarem
 * crus à tela, `600.00 + 400.00` vira `"600.00400.00"` e ninguém percebe até
 * um total absurdo aparecer no painel. Toda resposta passa por normalização.
 */

const CAMPOS_NUMERICOS_POSICAO = [
  'base_amount',
  'fine_amount',
  'interest_amount',
  'total_due',
  'paid_amount',
  'balance',
] as const

const CAMPOS_NUMERICOS_COBRANCA = [
  'rent_amount',
  'charges_amount',
  'discount_amount',
  'fine_rate',
  'interest_rate',
] as const

const paraNumero = (valor: unknown): number => {
  if (typeof valor === 'number') return valor
  if (typeof valor === 'string') {
    const n = parseFloat(valor)
    return Number.isNaN(n) ? 0 : n
  }
  return 0
}

const normalizarCobranca = <T extends Record<string, any>>(charge: T): T => {
  if (!charge || typeof charge !== 'object') return charge

  CAMPOS_NUMERICOS_COBRANCA.forEach((campo) => {
    if (charge[campo] !== undefined && charge[campo] !== null) {
      ;(charge as any)[campo] = paraNumero(charge[campo])
    }
  })

  if (charge.position) {
    CAMPOS_NUMERICOS_POSICAO.forEach((campo) => {
      if (charge.position[campo] !== undefined && charge.position[campo] !== null) {
        charge.position[campo] = paraNumero(charge.position[campo])
      }
    })
  }

  if (Array.isArray(charge.entries)) {
    charge.entries.forEach((entry: any) => {
      entry.amount = paraNumero(entry.amount)
    })
  }

  return charge
}

export class ChargesService {
  private readonly endpoint = '/charges'

  async getCharges(filters?: ChargeFilters): Promise<Charge[]> {
    const queryString = filters ? buildQueryString(filters as Record<string, any>) : ''
    const dados = await apiClient.get<Charge[]>(`${this.endpoint}/${queryString}`)
    return (dados || []).map(normalizarCobranca)
  }

  async getCharge(id: number): Promise<ChargeDetail> {
    return normalizarCobranca(await apiClient.get<ChargeDetail>(`${this.endpoint}/${id}`))
  }

  /** Emite as cobranças da competência. Idempotente — pode chamar duas vezes. */
  async generate(competencia?: string, contractId?: number): Promise<GenerateChargesResult> {
    return apiClient.post<GenerateChargesResult>(`${this.endpoint}/generate`, {
      competencia: competencia ?? null,
      contract_id: contractId ?? null,
    })
  }

  /**
   * Registra um recebimento — inclusive PARCIAL.
   *
   * É o caminho para "o aluguel é 1.000 e ele pagou 600": o saldo restante
   * continua existindo na mesma cobrança, em vez de virar dívida nova.
   */
  async addEntry(chargeId: number, entry: PaymentEntryInput): Promise<ChargeDetail> {
    return normalizarCobranca(
      await apiClient.post<ChargeDetail>(`${this.endpoint}/${chargeId}/entries`, entry)
    )
  }

  /**
   * Quita a cobrança pelo saldo exato do dia.
   *
   * Preferível a montar o valor na tela: multa e juros são calculados no
   * servidor, e duplicar esse cálculo no cliente gera divergência de centavos.
   */
  async settle(chargeId: number, paymentDate?: string, method?: string): Promise<ChargeDetail> {
    const query = buildQueryString({ payment_date: paymentDate, method })
    return normalizarCobranca(
      await apiClient.post<ChargeDetail>(`${this.endpoint}/${chargeId}/settle${query}`, {})
    )
  }

  async getEntries(chargeId: number): Promise<PaymentEntry[]> {
    const dados = await apiClient.get<PaymentEntry[]>(`${this.endpoint}/${chargeId}/entries`)
    return (dados || []).map((e) => ({ ...e, amount: paraNumero(e.amount) }))
  }

  /** Estorna um recebimento lançado por engano. */
  async deleteEntry(chargeId: number, entryId: number): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(
      `${this.endpoint}/${chargeId}/entries/${entryId}`
    )
  }

  /** Cancela preservando o histórico — não apaga os recebimentos aplicados. */
  async cancel(chargeId: number): Promise<ChargeDetail> {
    return normalizarCobranca(
      await apiClient.post<ChargeDetail>(`${this.endpoint}/${chargeId}/cancel`, {})
    )
  }

  async deleteCharge(chargeId: number): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`${this.endpoint}/${chargeId}`)
  }

  /** Vencidos por faixa (1-30 / 31-60 / 61-90 / 90+), somando saldo. */
  async getAging(): Promise<AgingReport> {
    const dados = await apiClient.get<AgingReport>(`${this.endpoint}/aging`)
    return {
      ...dados,
      total_open: paraNumero(dados.total_open),
      total_overdue: paraNumero(dados.total_overdue),
      buckets: (dados.buckets || []).map((b) => ({ ...b, amount: paraNumero(b.amount) })),
    }
  }

  async getDelinquency(limit = 50): Promise<DelinquencyRow[]> {
    const dados = await apiClient.get<DelinquencyRow[]>(
      `${this.endpoint}/delinquency${buildQueryString({ limit })}`
    )
    return (dados || []).map((linha) => ({
      ...linha,
      balance: paraNumero(linha.balance),
      overdue_balance: paraNumero(linha.overdue_balance),
    }))
  }

  /** Extrato do inquilino: saldo, atraso mais antigo e histórico de pontualidade. */
  async getTenantLedger(tenantId: number): Promise<TenantLedger> {
    const dados = await apiClient.get<TenantLedger>(`/tenants/${tenantId}/ledger`)
    return {
      ...dados,
      open_balance: paraNumero(dados.open_balance),
      overdue_balance: paraNumero(dados.overdue_balance),
      entries: (dados.entries || []).map((e) => normalizarCobranca(e as any)),
    }
  }
}

export const chargesService = new ChargesService()
