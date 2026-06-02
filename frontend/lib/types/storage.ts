// ============================================
// Storage Types — Supabase Direct Upload
// ============================================

/** Buckets configurados no Supabase Storage */
export type StorageBucket = 'public-assets' | 'private-documents'

/** Categorias de upload por entidade */
export type UploadCategory = 'imoveis' | 'inquilinos' | 'despesas'

/** Mapeamento categoria → bucket */
export const CATEGORY_BUCKET_MAP: Record<UploadCategory, StorageBucket> = {
  imoveis: 'public-assets',
  inquilinos: 'private-documents',
  despesas: 'private-documents',
}

/** Resultado individual de um upload */
export interface UploadResult {
  /** Caminho completo no bucket (ex: "42/imoveis/5/20260226_143000_foto.jpg") */
  path: string
  /** URL pública — preenchida apenas para bucket public-assets */
  publicUrl?: string
}

/** Opções para upload de arquivo(s) */
export interface UploadOptions {
  bucket: StorageBucket
  category: UploadCategory
  entityId: string | number
  userId: string
  onProgress?: (percent: number) => void
}

// ============================================
// Validação de arquivos
// ============================================

/** Tipos MIME permitidos para imagens */
export const ALLOWED_IMAGE_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
  'image/svg+xml',
]

/** Tipos MIME permitidos para documentos */
export const ALLOWED_DOC_TYPES = [
  'image/jpeg',
  'image/png',
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'text/plain',
]

/** Todos os tipos permitidos (imagens + documentos) */
export const ALLOWED_ALL_TYPES = [...new Set([...ALLOWED_IMAGE_TYPES, ...ALLOWED_DOC_TYPES])]

/** Extensões legíveis — para mensagens de erro */
export const ALLOWED_IMAGE_EXTENSIONS = '.jpg, .png, .gif, .webp, .svg'
export const ALLOWED_DOC_EXTENSIONS = '.jpg, .png, .pdf, .doc, .docx, .xls, .xlsx, .txt'

/** Tamanho máximo de arquivo: 10 MB */
export const MAX_FILE_SIZE = 10 * 1024 * 1024

/** Máximo de arquivos por upload */
export const MAX_FILES_PER_UPLOAD = 10
