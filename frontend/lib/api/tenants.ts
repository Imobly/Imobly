import { apiClient, buildQueryString } from './client'
import {
  TenantResponse,
  TenantCreate,
  TenantUpdate,
  TenantFilters,
  TenantDocument,
} from '@/lib/types/api'
import { uploadTenantDocuments as storageUploadDocs, deleteFile, getSignedUrl } from '@/lib/services/storage'

export class TenantsService {
  private readonly endpoint = '/tenants'

  // Listar inquilinos com filtros
  async getTenants(filters?: TenantFilters): Promise<TenantResponse[]> {
    const queryString = filters ? buildQueryString(filters) : ''
    return apiClient.get<TenantResponse[]>(`${this.endpoint}/${queryString}`)
  }

  // Obter inquilino por ID
  async getTenant(id: number): Promise<TenantResponse> {
    return apiClient.get<TenantResponse>(`${this.endpoint}/${id}`)
  }

  // Obter inquilino por email
  async getTenantByEmail(email: string): Promise<TenantResponse> {
    return apiClient.get<TenantResponse>(`${this.endpoint}/by-email/${encodeURIComponent(email)}/`)
  }

  // Obter inquilino por CPF
  async getTenantByCpf(cpf: string): Promise<TenantResponse> {
    return apiClient.get<TenantResponse>(`${this.endpoint}/by-cpf/${encodeURIComponent(cpf)}/`)
  }

  // Criar novo inquilino
  async createTenant(tenant: TenantCreate): Promise<TenantResponse> {
    return apiClient.post<TenantResponse>(`${this.endpoint}/`, tenant)
  }

  // Atualizar inquilino
  async updateTenant(id: number, tenant: TenantUpdate): Promise<TenantResponse> {
    return apiClient.put<TenantResponse>(`${this.endpoint}/${id}`, tenant)
  }

  // Deletar inquilino
  async deleteTenant(id: number): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`${this.endpoint}/${id}`)
  }

  // Upload de documentos do inquilino (direto ao Supabase)
  async uploadDocuments(
    tenantId: number,
    files: File[],
    documentType: 'rg' | 'cpf' | 'cnh' | 'comprovante_residencia' | 'comprovante_renda' | 'contrato' | 'outros',
    userId: string,
    existingDocuments: TenantDocument[] = [],
    onProgress?: (progress: number) => void
  ): Promise<{
    message: string
    uploaded_files: TenantDocument[]
    total_documents: number
  }> {
    // 1. Upload direto ao Supabase → bucket private-documents
    const results = await storageUploadDocs(files, tenantId, userId, onProgress)

    // 2. Construir objetos TenantDocument
    const newDocs: TenantDocument[] = results.map((r, i) => ({
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
    await this.updateTenant(tenantId, { documents: merged })

    return {
      message: `${newDocs.length} documento(s) enviado(s)`,
      uploaded_files: newDocs,
      total_documents: merged.length,
    }
  }

  // Listar documentos do inquilino (com signed URLs)
  async getDocuments(tenantId: number): Promise<{
    tenant_id: number
    tenant_name: string
    documents: TenantDocument[]
    total_documents: number
  }> {
    return apiClient.get(`${this.endpoint}/${tenantId}/documents`)
  }

  // Gerar URL temporária para visualizar documento privado
  async getDocumentSignedUrl(path: string): Promise<string> {
    return getSignedUrl(path)
  }

  // Deletar documento do inquilino
  async deleteDocument(
    tenantId: number,
    documentPath: string,
    existingDocuments: TenantDocument[] = []
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
    await this.updateTenant(tenantId, { documents: remaining })

    return {
      message: 'Documento removido com sucesso',
      remaining_documents: remaining.length,
    }
  }
}

// Instância singleton do serviço
export const tenantsService = new TenantsService()