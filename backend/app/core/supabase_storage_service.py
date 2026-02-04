"""
Serviço de upload para Supabase Storage
Gerencia upload, download e deleção de arquivos no Supabase
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import HTTPException, UploadFile, status

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

from app.core.config import settings


class SupabaseStorageService:
    """Serviço para gerenciar uploads no Supabase Storage"""

    ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx"}
    ALLOWED_ALL_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS

    # Mapeamento de pastas para buckets
    BUCKET_MAPPING = {
        "properties": "property-images",
        "tenants": "tenant-documents",
        "expenses": "expense-documents",
    }

    def __init__(self):
        if not SUPABASE_AVAILABLE:
            raise ImportError(
                "Supabase client não instalado. Execute: pip install supabase"
            )
        
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Variáveis SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY devem estar configuradas"
            )
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.max_file_size = settings.MAX_FILE_SIZE

    def _get_bucket_name(self, folder: str) -> str:
        """Determina o bucket com base na pasta"""
        # Extrair categoria da pasta (ex: "properties/123" -> "properties")
        category = folder.split("/")[0]
        return self.BUCKET_MAPPING.get(category, "property-images")

    def _validate_file_extension(
        self, filename: str, allowed_types: Literal["image", "document", "all"]
    ) -> bool:
        """Valida a extensão do arquivo"""
        ext = Path(filename).suffix.lower()

        if allowed_types == "image":
            return ext in self.ALLOWED_IMAGE_EXTENSIONS
        elif allowed_types == "document":
            return ext in self.ALLOWED_DOCUMENT_EXTENSIONS
        else:  # all
            return ext in self.ALLOWED_ALL_EXTENSIONS

    def _generate_unique_filename(self, original_filename: str) -> str:
        """Gera um nome único para o arquivo"""
        ext = Path(original_filename).suffix.lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{timestamp}_{unique_id}{ext}"

    def _get_content_type(self, filename: str) -> str:
        """Determina o content-type baseado na extensão"""
        ext = Path(filename).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        return mime_types.get(ext, "application/octet-stream")

    async def save_file(
        self,
        file: UploadFile,
        folder: str,
        allowed_types: Literal["image", "document", "all"] = "all",
    ) -> dict:
        """
        Salva um arquivo no Supabase Storage

        Args:
            file: Arquivo a ser salvo
            folder: Pasta de destino (ex: 'properties/123')
            allowed_types: Tipo de arquivo permitido

        Returns:
            dict com informações do arquivo salvo
        """
        # Validar nome do arquivo
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome do arquivo não pode ser vazio",
            )

        # Validar extensão
        if not self._validate_file_extension(file.filename, allowed_types):
            allowed_exts = (
                self.ALLOWED_IMAGE_EXTENSIONS
                if allowed_types == "image"
                else self.ALLOWED_DOCUMENT_EXTENSIONS
                if allowed_types == "document"
                else self.ALLOWED_ALL_EXTENSIONS
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de arquivo não permitido. Extensões aceitas: {', '.join(allowed_exts)}",
            )

        # Ler conteúdo do arquivo
        content = await file.read()
        file_size = len(content)

        # Validar tamanho
        if file_size > self.max_file_size:
            max_mb = self.max_file_size / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Arquivo muito grande. Tamanho máximo: {max_mb}MB",
            )

        # Gerar nome único e path
        unique_filename = self._generate_unique_filename(file.filename)
        file_path = f"{folder}/{unique_filename}"

        # Determinar bucket
        bucket_name = self._get_bucket_name(folder)

        # Upload para Supabase
        try:
            print(f"🔄 Tentando upload para Supabase...")
            print(f"   Bucket: {bucket_name}")
            print(f"   Path: {file_path}")
            print(f"   Size: {file_size} bytes")
            
            self.client.storage.from_(bucket_name).upload(
                file_path,
                content,
                file_options={
                    "content-type": self._get_content_type(file.filename),
                    "cache-control": "3600",
                }
            )
            print(f"✅ Upload concluído com sucesso!")
        except Exception as e:
            print(f"❌ Erro no upload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao fazer upload: {str(e)}",
            )

        # Gerar URL do arquivo
        if bucket_name == "property-images":
            # URL pública para imagens
            file_url = self.client.storage.from_(bucket_name).get_public_url(file_path)
        else:
            # URL assinada para documentos privados (válida por 1 ano)
            signed_url_response = self.client.storage.from_(bucket_name).create_signed_url(
                file_path, expires_in=31536000
            )
            file_url = signed_url_response.get("signedURL", "")

        file_type = Path(file.filename).suffix.lower()[1:]  # Remove o ponto

        return {
            "filename": unique_filename,
            "original_filename": file.filename,
            "url": file_url,
            "size": file_size,
            "type": file_type,
            "bucket": bucket_name,
            "path": file_path,
        }

    async def save_multiple_files(
        self,
        files: List[UploadFile],
        folder: str,
        allowed_types: Literal["image", "document", "all"] = "all",
        max_files: int = 10,
    ) -> List[dict]:
        """Salva múltiplos arquivos"""
        if len(files) > max_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Número máximo de arquivos excedido. Máximo: {max_files}",
            )

        saved_files = []
        for file in files:
            file_info = await self.save_file(file, folder, allowed_types)
            saved_files.append(file_info)

        return saved_files

    def delete_file(self, file_url: str) -> bool:
        """
        Deleta um arquivo do Supabase Storage

        Args:
            file_url: URL do arquivo (pode ser pública ou assinada)

        Returns:
            True se deletado com sucesso
        """
        try:
            # Extrair path do arquivo da URL
            # URL pública: https://projeto.supabase.co/storage/v1/object/public/bucket/path
            # URL assinada: https://projeto.supabase.co/storage/v1/object/sign/bucket/path?token=...
            
            print(f"🗑️  Tentando deletar: {file_url}")
            
            # Remover query string (token)
            clean_url = file_url.split("?")[0] if "?" in file_url else file_url
            
            # Extrair a parte após '/storage/v1/object/'
            if "/storage/v1/object/" not in clean_url:
                print(f"❌ URL inválida: não contém '/storage/v1/object/'")
                return False
            
            parts = clean_url.split("/storage/v1/object/")
            url_path = parts[1]  # Ex: 'sign/tenant-documents/tenants/4/file.pdf' ou 'public/bucket/path'
            
            # Remove 'public/' ou 'sign/' do início
            if url_path.startswith("public/"):
                url_path = url_path[7:]  # Remove 'public/'
            elif url_path.startswith("sign/"):
                url_path = url_path[5:]  # Remove 'sign/'
            
            # Agora temos: 'tenant-documents/tenants/4/file.pdf'
            # Primeiro elemento é o bucket, resto é o path
            path_parts = url_path.split("/", 1)
            if len(path_parts) < 2:
                print(f"❌ Path inválido: {url_path}")
                return False
            
            bucket_name = path_parts[0]
            file_path = path_parts[1]
            
            print(f"   Bucket: {bucket_name}")
            print(f"   Path: {file_path}")

            # Deletar do Supabase
            result = self.client.storage.from_(bucket_name).remove([file_path])
            print(f"✅ Arquivo deletado com sucesso!")
            return True
        
        except Exception as e:
            print(f"❌ Erro ao deletar arquivo: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def delete_multiple_files(self, file_urls: List[str]) -> dict:
        """Deleta múltiplos arquivos"""
        deleted = 0
        failed = 0

        for url in file_urls:
            if self.delete_file(url):
                deleted += 1
            else:
                failed += 1

        return {"deleted": deleted, "failed": failed}

    def get_signed_url(self, file_path: str, bucket_name: str, expires_in: int = 3600) -> str:
        """
        Gera URL assinada para acesso temporário a arquivos privados

        Args:
            file_path: Path do arquivo no bucket
            bucket_name: Nome do bucket
            expires_in: Tempo de expiração em segundos (padrão: 1 hora)

        Returns:
            URL assinada
        """
        try:
            response = self.client.storage.from_(bucket_name).create_signed_url(
                file_path, expires_in=expires_in
            )
            return response.get("signedURL", "")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao gerar URL assinada: {str(e)}",
            )


# Instância singleton do serviço
try:
    supabase_storage_service = SupabaseStorageService()
except (ImportError, ValueError) as e:
    print(f"⚠️  Supabase Storage não disponível: {str(e)}")
    supabase_storage_service = None
