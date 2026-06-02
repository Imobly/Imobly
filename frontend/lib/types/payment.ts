import { PaymentResponse } from './api'

export interface Payment {
  id: number
  property_id: number
  tenant_id: number
  contract_id: number
  property?: {
    id: number
    name: string
    address: string
  }
  tenant?: {
    id: number
    name: string
    email: string
  }
  contract?: {
    id: number
    title: string
  }
  dueDate: string
  due_date?: string // compatibilidade com API
  paymentDate: string | null
  payment_date?: string | null // compatibilidade com API
  amount: number
  fineAmount: number
  fine_amount?: number // compatibilidade com API
  totalAmount: number
  total_amount?: number // compatibilidade com API
  status: 'pendente' | 'pago' | 'atrasado' | 'parcial'
  paymentMethod: 'cash' | 'transfer' | 'pix' | 'check' | 'card' | null
  payment_method?: 'cash' | 'transfer' | 'pix' | 'check' | 'card' | null // compatibilidade com API
  description?: string
  createdAt?: string
  created_at?: string // compatibilidade com API
  updated_at?: string
}

export interface PaymentFormData {
  id?: number
  property_id?: number
  tenant_id?: number
  contract_id?: number
  property?: {
    id: number
    name: string
    address: string
  } | null
  tenant?: {
    id: number
    name: string
    email: string
  } | null
  contract?: {
    id: number
    title: string
  } | null
  dueDate: string
  due_date?: string
  paymentDate: string | null
  payment_date?: string | null
  amount: number
  fineAmount: number
  fine_amount?: number
  totalAmount: number
  total_amount?: number
  status: 'pendente' | 'pago' | 'atrasado' | 'parcial'
  paymentMethod: 'cash' | 'transfer' | 'pix' | 'check' | 'card' | null
  payment_method?: 'cash' | 'transfer' | 'pix' | 'check' | 'card' | null
  description?: string
  createdAt?: string
  created_at?: string
  updated_at?: string
}

// Função utilitária para conversão
export const convertApiToPayment = (apiPayment: PaymentResponse): Payment => ({
  id: apiPayment.id,
  property_id: apiPayment.property_id,
  tenant_id: apiPayment.tenant_id,
  contract_id: apiPayment.contract_id,
  dueDate: apiPayment.due_date,
  due_date: apiPayment.due_date,
  paymentDate: apiPayment.payment_date || null,
  payment_date: apiPayment.payment_date || null,
  amount: Number(apiPayment.amount) || 0,
  fineAmount: Number(apiPayment.fine_amount) || 0,
  fine_amount: Number(apiPayment.fine_amount) || 0,
  totalAmount: Number(apiPayment.total_amount) || 0,
  total_amount: Number(apiPayment.total_amount) || 0,
  status: apiPayment.status,
  paymentMethod: apiPayment.payment_method || null,
  payment_method: apiPayment.payment_method,
  description: apiPayment.description,
  createdAt: apiPayment.created_at,
  created_at: apiPayment.created_at,
  updated_at: apiPayment.updated_at
})