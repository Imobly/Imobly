import { apiClient, buildQueryString } from './client'
import {
  PropertyResponse,
  PropertyCreate,
  PropertyUpdate,
  PropertyFilters,
} from '@/lib/types/api'
import { uploadPropertyImages as storageUploadImages, deleteFile } from '@/lib/services/storage'

export class PropertiesService {
  private readonly endpoint = '/properties'

  // Listar propriedades com filtros
  async getProperties(filters?: PropertyFilters): Promise<PropertyResponse[]> {
    const queryString = filters ? buildQueryString(filters) : ''
    return apiClient.get<PropertyResponse[]>(`${this.endpoint}/${queryString}`)
  }

  // Listar apenas propriedades disponíveis
  async getAvailableProperties(): Promise<PropertyResponse[]> {
    return apiClient.get<PropertyResponse[]>(`${this.endpoint}/available`)
  }

  // Obter propriedade por ID
  async getProperty(id: number): Promise<PropertyResponse> {
    return apiClient.get<PropertyResponse>(`${this.endpoint}/${id}`)
  }

  // Criar nova propriedade
  async createProperty(property: PropertyCreate): Promise<PropertyResponse> {
    return apiClient.post<PropertyResponse>(`${this.endpoint}/`, property)
  }

  // Atualizar propriedade
  async updateProperty(id: number, property: PropertyUpdate): Promise<PropertyResponse> {
    return apiClient.put<PropertyResponse>(`${this.endpoint}/${id}`, property)
  }

  // Atualizar apenas o status da propriedade
  async updatePropertyStatus(id: number, status: string): Promise<PropertyResponse> {
    return apiClient.patch<PropertyResponse>(`${this.endpoint}/${id}/status/?status=${status}`)
  }

  // Deletar propriedade
  async deleteProperty(id: number): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`${this.endpoint}/${id}`)
  }

  // Upload de imagens da propriedade (direto ao Supabase)
  async uploadImages(
    propertyId: number,
    files: File[],
    userId: string,
    existingImages: string[] = [],
    onProgress?: (progress: number) => void
  ): Promise<{
    images: string[]
    property: PropertyResponse
  }> {
    // 1. Upload direto ao Supabase → bucket public-assets
    const results = await storageUploadImages(files, propertyId, userId, onProgress)
    const newUrls = results.map(r => r.publicUrl!)

    // 2. Atualizar registro no backend via PUT
    const updatedImages = [...existingImages, ...newUrls]
    const property = await this.updateProperty(propertyId, { images: updatedImages })

    return { images: newUrls, property }
  }

  // Deletar imagem da propriedade
  async deleteImage(
    propertyId: number,
    imageIndex: number,
    currentImages: string[] = []
  ): Promise<{
    message: string
    property: PropertyResponse
  }> {
    // Tentar extrair path do Supabase da URL para deletar do storage
    const imageUrl = currentImages[imageIndex]
    if (imageUrl) {
      try {
        const url = new URL(imageUrl)
        const pathMatch = url.pathname.match(/\/object\/public\/public-assets\/(.+)/)
        if (pathMatch) {
          await deleteFile(pathMatch[1], 'public-assets')
        }
      } catch {
        // Se falhar a exclusão do storage, continua removendo do DB
      }
    }

    // Remover URL do array e atualizar via PUT
    const updatedImages = currentImages.filter((_, i) => i !== imageIndex)
    const property = await this.updateProperty(propertyId, { images: updatedImages })

    return { message: 'Imagem removida com sucesso', property }
  }
}

// Instância singleton do serviço
export const propertiesService = new PropertiesService()