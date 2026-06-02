import { apiClient, buildQueryString } from './client'
import {
  PaymentResponse,
  PaymentCreate,
  PaymentUpdate,
  PaymentFilters,
  PaymentConfirm,
  BulkPaymentConfirm,
} from '@/lib/types/api'

export class PaymentsService {
  private readonly endpoint = '/payments'

  // Converte campos numéricos que chegam como string do backend para number
  private normalizeCalculationPayload(payload: any) {
    if (!payload || typeof payload !== 'object') return payload
    const numericKeys = [
      'base_amount',
      'fine_amount',
      'interest_amount',
      'total_addition',
      'total_expected',
      'paid_amount',
      'remaining_amount'
    ]
    numericKeys.forEach(k => {
      if (payload[k] !== undefined && payload[k] !== null) {
        const value = payload[k]
        // Backend envia alguns campos com alta precisão (ex: interest_amount)
        // Garantimos parseFloat seguro, mantendo possível precisão para cálculos posteriores.
        const parsed = typeof value === 'string' ? parseFloat(value) : value
        if (!isNaN(parsed)) payload[k] = parsed
      }
    })
    return payload
  }

  private normalizeRegisterResponse(payload: any) {
    if (!payload || typeof payload !== 'object') return payload
    const numericKeys = [
      'amount',
      'fine_amount',
      'total_amount'
    ]
    numericKeys.forEach(k => {
      if (payload[k] !== undefined && payload[k] !== null) {
        const value = payload[k]
        const parsed = typeof value === 'string' ? parseFloat(value) : value
        if (!isNaN(parsed)) payload[k] = parsed
      }
    })
    return payload
  }

  // Listar pagamentos com filtros
  async getPayments(filters?: PaymentFilters): Promise<PaymentResponse[]> {
    const queryString = filters ? buildQueryString(filters) : ''
    return apiClient.get<PaymentResponse[]>(`${this.endpoint}/${queryString}`)
  }

  // Obter pagamento por ID
  async getPayment(id: number): Promise<PaymentResponse> {
    return apiClient.get<PaymentResponse>(`${this.endpoint}/${id}`)
  }

  // Criar novo pagamento
  async createPayment(payment: PaymentCreate): Promise<PaymentResponse> {
    return apiClient.post<PaymentResponse>(`${this.endpoint}/`, payment)
  }

  // Atualizar pagamento
  async updatePayment(id: number, payment: PaymentUpdate): Promise<PaymentResponse> {
    return apiClient.put<PaymentResponse>(`${this.endpoint}/${id}`, payment)
  }

  // Confirmar pagamento
  async confirmPayment(id: number, confirmation?: PaymentConfirm): Promise<PaymentResponse> {
    const data = confirmation || {}
    return apiClient.post<PaymentResponse>(`${this.endpoint}/${id}/confirm/`, data)
  }

  // Obter pagamentos em atraso
  async getOverduePayments(): Promise<PaymentResponse[]> {
    return apiClient.get<PaymentResponse[]>(`${this.endpoint}/overdue/list`)
  }

  // Confirmar múltiplos pagamentos
  async bulkConfirmPayments(data: BulkPaymentConfirm): Promise<PaymentResponse[]> {
    return apiClient.post<PaymentResponse[]>(`${this.endpoint}/bulk-confirm/`, data)
  }

  // Excluir pagamento
  async deletePayment(id: number): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`${this.endpoint}/${id}`)
  }

  // Calcular valores de pagamento (multa, juros, total)
  async calculatePayment(data: {
    contract_id: number;
    due_date: string;
    payment_date?: string;
    paid_amount?: number;
  }): Promise<{
    base_amount: number;
    fine_amount: number;
    interest_amount: number;
    total_addition: number;
    total_expected: number;
    days_overdue: number;
    status: string;
    paid_amount: number;
    remaining_amount: number;
  }> {
    const raw = await apiClient.post(`${this.endpoint}/calculate`, data)
    const normalized = this.normalizeCalculationPayload(raw)
    // Ajuste de status: se houver dias de atraso, marcamos como atrasado
    if (normalized && typeof normalized.days_overdue === 'number' && normalized.days_overdue > 0) {
      normalized.status = 'atrasado'
    }
    return normalized
  }

  // Registrar pagamento com cálculo automático
  async registerPayment(data: {
    contract_id: number;
    property_id?: number;
    tenant_id?: number;
    due_date: string;
    payment_date: string;
    paid_amount: number;
    payment_method?: 'pix' | 'boleto' | 'transferencia' | 'dinheiro' | 'cartao_credito' | 'cartao_debito' | 'outro';
    description?: string;
  }): Promise<PaymentResponse> {
    const raw = await apiClient.post<PaymentResponse>(`${this.endpoint}/register`, data)
    return this.normalizeRegisterResponse(raw)
  }
}

// Instância singleton do serviço
export const paymentsService = new PaymentsService()