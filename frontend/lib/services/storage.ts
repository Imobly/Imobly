// ============================================
// StorageService — Upload direto ao Supabase
// ============================================

import { getAuthenticatedClient } from '@/lib/supabase'
import {
  type StorageBucket,
  type UploadCategory,
  type UploadResult,
  type UploadOptions,
  CATEGORY_BUCKET_MAP,
  ALLOWED_IMAGE_TYPES,
  ALLOWED_DOC_TYPES,
  ALLOWED_ALL_TYPES,
  ALLOWED_IMAGE_EXTENSIONS,
  ALLOWED_DOC_EXTENSIONS,
  MAX_FILE_SIZE,
  MAX_FILES_PER_UPLOAD,
} from '@/lib/types/storage'

// ============================================
// Helpers
// ============================================

/**
 * Remove acentos, espaços e caracteres especiais de um nome de arquivo.
 * Mantém apenas letras, números, hifens, underscores e o ponto da extensão.
 */
function sanitizeFilename(name: string): string {
  // Separar nome e extensão
  const lastDot = name.lastIndexOf('.')
  const baseName = lastDot > 0 ? name.slice(0, lastDot) : name
  const ext = lastDot > 0 ? name.slice(lastDot) : ''

  const sanitized = baseName
    .normalize('NFD')                          // decompor acentos
    .replace(/[\u0300-\u036f]/g, '')           // remover diacríticos
    .replace(/\s+/g, '-')                      // espaços → hifens
    .replace(/[^a-zA-Z0-9\-_]/g, '')          // remover caracteres especiais
    .toLowerCase()

  return `${sanitized || 'file'}${ext.toLowerCase()}`
}

/**
 * Gera timestamp no formato YYYYMMDD_HHmmss
 */
function timestamp(): string {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return (
    `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}` +
    `_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`
  )
}

/**
 * Monta o path do arquivo no bucket.
 * Padrão: {userId}/{category}/{entityId}/{timestamp}_{sanitizedFilename}
 */
function buildPath(
  userId: string,
  category: UploadCategory,
  entityId: string | number,
  filename: string,
): string {
  return `${userId}/${category}/${entityId}/${timestamp()}_${sanitizeFilename(filename)}`
}

/**
 * Valida tipo MIME e tamanho do arquivo.
 * @throws Error com mensagem descritiva
 */
function validateFile(
  file: File,
  allowedTypes: string[],
  maxSize: number = MAX_FILE_SIZE,
): void {
  if (!allowedTypes.includes(file.type)) {
    const isImageOnly = allowedTypes === ALLOWED_IMAGE_TYPES
    const extensions = isImageOnly ? ALLOWED_IMAGE_EXTENSIONS : ALLOWED_DOC_EXTENSIONS
    throw new Error(
      `Tipo de arquivo não permitido: "${file.name}". Tipos aceitos: ${extensions}`,
    )
  }

  if (file.size > maxSize) {
    const maxMB = Math.round(maxSize / (1024 * 1024))
    throw new Error(
      `Arquivo "${file.name}" excede o tamanho máximo de ${maxMB}MB (${(file.size / (1024 * 1024)).toFixed(1)}MB).`,
    )
  }
}

// ============================================
// Core upload / delete / signed URL
// ============================================

/**
 * Faz upload de um único arquivo para o Supabase Storage.
 * - Bucket `public-assets`: retorna publicUrl
 * - Bucket `private-documents`: retorna apenas path (use getSignedUrl para acessar)
 */
export async function uploadFile(
  file: File,
  options: UploadOptions,
): Promise<UploadResult> {
  const { bucket, category, entityId, userId } = options
  const allowedTypes = bucket === 'public-assets' ? ALLOWED_IMAGE_TYPES : ALLOWED_ALL_TYPES

  validateFile(file, allowedTypes)

  const path = buildPath(userId, category, entityId, file.name)
  const client = await getAuthenticatedClient()

  const { error } = await client.storage
    .from(bucket)
    .upload(path, file, {
      cacheControl: '3600',
      upsert: true,
    })

  if (error) {
    throw new Error(`Erro ao enviar "${file.name}": ${error.message}`)
  }

  const result: UploadResult = { path }

  if (bucket === 'public-assets') {
    const { data } = client.storage.from(bucket).getPublicUrl(path)
    result.publicUrl = data.publicUrl
  }

  return result
}

/**
 * Faz upload de múltiplos arquivos sequencialmente.
 * Retorna array de resultados na mesma ordem dos arquivos.
 * @throws Error no primeiro arquivo que falhar
 */
export async function uploadMultipleFiles(
  files: File[],
  options: UploadOptions,
): Promise<UploadResult[]> {
  if (files.length > MAX_FILES_PER_UPLOAD) {
    throw new Error(`Máximo de ${MAX_FILES_PER_UPLOAD} arquivos por upload.`)
  }

  const results: UploadResult[] = []

  for (let i = 0; i < files.length; i++) {
    const result = await uploadFile(files[i], options)
    // Simular progresso por arquivo (0-100 distribuído entre os arquivos)
    options.onProgress?.(Math.round(((i + 1) / files.length) * 100))
    results.push(result)
  }

  return results
}

/**
 * Remove um arquivo do Supabase Storage.
 */
export async function deleteFile(
  path: string,
  bucket: StorageBucket,
): Promise<void> {
  const client = await getAuthenticatedClient()
  const { error } = await client.storage.from(bucket).remove([path])

  if (error) {
    throw new Error(`Erro ao excluir arquivo: ${error.message}`)
  }
}

/**
 * Gera uma URL temporária (signed) para acessar um arquivo no bucket privado.
 * @param path Caminho do arquivo no bucket
 * @param expiresIn Duração em segundos (padrão: 1 hora)
 */
export async function getSignedUrl(
  path: string,
  expiresIn: number = 3600,
): Promise<string> {
  const client = await getAuthenticatedClient()
  const { data, error } = await client.storage
    .from('private-documents')
    .createSignedUrl(path, expiresIn)

  if (error || !data?.signedUrl) {
    throw new Error(`Erro ao gerar link: ${error?.message ?? 'URL não disponível'}`)
  }

  return data.signedUrl
}

// ============================================
// Convenience wrappers por entidade
// ============================================

/**
 * Upload de imagens de imóveis → bucket `public-assets`
 * Retorna array de publicUrls.
 */
export async function uploadPropertyImages(
  files: File[],
  propertyId: number,
  userId: string,
  onProgress?: (percent: number) => void,
): Promise<UploadResult[]> {
  return uploadMultipleFiles(files, {
    bucket: 'public-assets',
    category: 'imoveis',
    entityId: propertyId,
    userId,
    onProgress,
  })
}

/**
 * Upload de documentos de inquilinos → bucket `private-documents`
 * Retorna array de paths (usar getSignedUrl para acesso).
 */
export async function uploadTenantDocuments(
  files: File[],
  tenantId: number,
  userId: string,
  onProgress?: (percent: number) => void,
): Promise<UploadResult[]> {
  return uploadMultipleFiles(files, {
    bucket: 'private-documents',
    category: 'inquilinos',
    entityId: tenantId,
    userId,
    onProgress,
  })
}

/**
 * Upload de documentos/comprovantes de despesas → bucket `private-documents`
 * Retorna array de paths (usar getSignedUrl para acesso).
 */
export async function uploadExpenseDocuments(
  files: File[],
  expenseId: string,
  userId: string,
  onProgress?: (percent: number) => void,
): Promise<UploadResult[]> {
  return uploadMultipleFiles(files, {
    bucket: 'private-documents',
    category: 'despesas',
    entityId: expenseId,
    userId,
    onProgress,
  })
}

// Re-export types for convenience
export type { StorageBucket, UploadCategory, UploadResult, UploadOptions }
export {
  CATEGORY_BUCKET_MAP,
  ALLOWED_IMAGE_TYPES,
  ALLOWED_DOC_TYPES,
  MAX_FILE_SIZE,
  MAX_FILES_PER_UPLOAD,
  sanitizeFilename,
  buildPath,
}
