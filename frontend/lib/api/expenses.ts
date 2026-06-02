import { apiClient, buildQueryString } from './client'
import {
  ExpenseResponse,
  ExpenseCreate,
  ExpenseUpdate,
  ExpenseFilters,
  ExpenseSummary,
  ExpenseDocument,
} from '@/lib/types/api'
import { uploadExpenseDocuments as storageUploadDocs, deleteFile, getSignedUrl } from '@/lib/services/storage'

export class ExpensesService {
  private readonly endpoint = '/expenses'

  // Listar despesas com filtros
  async getExpenses(filters?: ExpenseFilters): Promise<ExpenseResponse[]> {
    const queryString = filters ? buildQueryString(filters) : ''
    return apiClient.get<ExpenseResponse[]>(`${this.endpoint}/${queryString}`)
  }

  // Obter despesa por ID
  async getExpense(id: string): Promise<ExpenseResponse> {
    return apiClient.get<ExpenseResponse>(`${this.endpoint}/${id}`)
  }

  // Criar nova despesa
  async createExpense(expense: ExpenseCreate): Promise<ExpenseResponse> {
    return apiClient.post<ExpenseResponse>(`${this.endpoint}/`, expense)
  }

  // Atualizar despesa
  async updateExpense(id: string, expense: ExpenseUpdate): Promise<ExpenseResponse> {
    return apiClient.put<ExpenseResponse>(`${this.endpoint}/${id}`, expense)
  }

  // Deletar despesa
  async deleteExpense(id: string): Promise<void> {
    return apiClient.delete<void>(`${this.endpoint}/${id}`)
  }

  // Obter despesas mensais de uma propriedade
  async getPropertyMonthlyExpenses(
    propertyId: number,
    year: number,
    month: number
  ): Promise<any> {
    return apiClient.get<any>(`${this.endpoint}/property/${propertyId}/monthly?year=${year}&month=${month}`)
  }

  // Obter resumo de despesas por categoria
  async getExpensesSummaryByCategory(filters?: {
    property_id?: number
    year?: number
    month?: number
  }): Promise<{ categories: ExpenseSummary[] }> {
    const queryString = filters ? buildQueryString(filters) : ''
    return apiClient.get<{ categories: ExpenseSummary[] }>(`${this.endpoint}/categories/summary${queryString}`)
  }

  // Upload de documentos da despesa (direto ao Supabase)
  async uploadDocuments(
    expenseId: string,
    files: File[],
    documentType: 'comprovante' | 'nota_fiscal' | 'recibo' | 'outros',
    userId: string,
    existingDocuments: ExpenseDocument[] = [],
    onProgress?: (progress: number) => void
  ): Promise<{
    message: string
    uploaded_files: ExpenseDocument[]
    total_documents: number
  }> {
    // 1. Upload direto ao Supabase → bucket private-documents
    const results = await storageUploadDocs(files, expenseId, userId, onProgress)

    // 2. Construir objetos ExpenseDocument
    const newDocs: ExpenseDocument[] = results.map((r, i) => ({
      id: crypto.randomUUID(),
      name: files[i].name,
      type: documentType,
      url: r.path,
      file_type: files[i].type,
      size: files[i].size,
      uploaded_at: new Date().toISOString(),
    }))

    // 3. Atualizar registro no backend via PUT
    const merged = [...existingDocuments, ...newDocs]
    await this.updateExpense(expenseId, { documents: merged })

    return {
      message: `${newDocs.length} documento(s) enviado(s)`,
      uploaded_files: newDocs,
      total_documents: merged.length,
    }
  }

  // Gerar URL temporária para visualizar documento privado
  async getDocumentSignedUrl(path: string): Promise<string> {
    return getSignedUrl(path)
  }

  // Deletar documento da despesa
  async deleteDocument(
    expenseId: string,
    documentPath: string,
    existingDocuments: ExpenseDocument[] = []
  ): Promise<{
    message: string
    remaining_documents: number
  }> {
    // 1. Deletar do Supabase Storage
    try {
      await deleteFile(documentPath, 'private-documents')
    } catch {
      // Se falhar a exclusão do storage, continua removendo do DB
    }

    // 2. Remover do array e atualizar via PUT
    const remaining = existingDocuments.filter(d => d.url !== documentPath)
    await this.updateExpense(expenseId, { documents: remaining })

    return {
      message: 'Documento removido com sucesso',
      remaining_documents: remaining.length,
    }
  }

  // Upload de comprovante da despesa (single file)
  async uploadReceipt(
    expenseId: string,
    file: File,
    userId: string,
    onProgress?: (progress: number) => void
  ): Promise<{
    message: string
    url: string
  }> {
    const results = await storageUploadDocs([file], expenseId, userId, onProgress)
    const path = results[0].path

    // Atualizar campo receipt no backend via PUT
    await this.updateExpense(expenseId, { receipt: path })

    return {
      message: 'Comprovante enviado com sucesso',
      url: path,
    }
  }

  // Deletar comprovante da despesa
  async deleteReceipt(
    expenseId: string,
    receiptPath: string
  ): Promise<{
    message: string
  }> {
    try {
      await deleteFile(receiptPath, 'private-documents')
    } catch {
      // Se falhar a exclusão do storage, continua
    }

    await this.updateExpense(expenseId, { receipt: undefined })

    return { message: 'Comprovante removido com sucesso' }
  }
}

// Instância singleton do serviço
export const expensesService = new ExpensesService()