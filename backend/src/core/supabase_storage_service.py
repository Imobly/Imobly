"""
Serviço para gerenciamento de arquivos no Supabase Storage
"""

from typing import Optional, List, Dict, Any
from fastapi import UploadFile, HTTPException, status
from supabase import Client
import logging
import os
from datetime import datetime
import mimetypes

logger = logging.getLogger(__name__)


class SupabaseStorageService:
    """Serviço para upload e gerenciamento de arquivos no Supabase Storage"""
    
    BUCKET_NAME = "users"
    ALLOWED_EXTENSIONS = {
        'images': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'},
        'documents': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt'},
        'all': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt'}
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.storage = supabase_client.storage
    
    def _validate_file(self, file: UploadFile, allowed_types: str = 'all') -> None:
        """
        Valida arquivo antes do upload
        
        Args:
            file: Arquivo para validação
            allowed_types: Tipo de arquivos permitidos ('images', 'documents', 'all')
            
        Raises:
            HTTPException: Se arquivo inválido
        """
        # Verifica extensão
        file_ext = os.path.splitext(file.filename or '')[1].lower()
        allowed_exts = self.ALLOWED_EXTENSIONS.get(allowed_types, self.ALLOWED_EXTENSIONS['all'])
        
        if file_ext not in allowed_exts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de arquivo não permitido. Extensões aceitas: {', '.join(allowed_exts)}"
            )
        
        # Verifica tamanho (se possível)
        if hasattr(file.file, 'seek') and hasattr(file.file, 'tell'):
            file.file.seek(0, 2)  # Move para o final
            file_size = file.file.tell()
            file.file.seek(0)  # Volta para o início
            
            if file_size > self.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Arquivo muito grande. Tamanho máximo: {self.MAX_FILE_SIZE / (1024*1024):.1f}MB"
                )
    
    def _generate_file_path(self, user_id: int, category: str, filename: str) -> str:
        """
        Gera caminho único para o arquivo no storage
        
        Args:
            user_id: ID do usuário
            category: Categoria do arquivo (properties, expenses, tenants)
            filename: Nome original do arquivo
            
        Returns:
            str: Caminho completo no formato users/{user_id}/{category}/{timestamp}_{filename}
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = filename.replace(' ', '_')
        return f"{user_id}/{category}/{timestamp}_{safe_filename}"
    
    async def upload_file(
        self,
        file: UploadFile,
        user_id: int,
        category: str,
        allowed_types: str = 'all'
    ) -> Dict[str, str]:
        """
        Faz upload de arquivo para o Supabase Storage
        
        Args:
            file: Arquivo para upload
            user_id: ID do usuário proprietário
            category: Categoria (properties, expenses, tenants)
            allowed_types: Tipo de arquivos permitidos
            
        Returns:
            Dict com path e public_url do arquivo
            
        Raises:
            HTTPException: Se erro no upload
        """
        try:
            # Valida arquivo
            self._validate_file(file, allowed_types)
            
            # Gera caminho
            file_path = self._generate_file_path(user_id, category, file.filename or 'file')
            
            # Lê conteúdo do arquivo
            file_content = await file.read()
            
            # Detecta content type
            content_type = file.content_type
            if not content_type:
                content_type = mimetypes.guess_type(file.filename or '')[0] or 'application/octet-stream'
            
            # Faz upload
            response = self.storage.from_(self.BUCKET_NAME).upload(
                path=file_path,
                file=file_content,
                file_options={
                    "content-type": content_type,
                    "upsert": "true"
                }
            )
            
            logger.info(f"📤 Upload response: {response}")
            
            # Gera URL pública
            public_url = self.storage.from_(self.BUCKET_NAME).get_public_url(file_path)
            
            logger.info(f"Arquivo enviado com sucesso: {file_path}")
            logger.info(f"URL pública gerada: {public_url}")
            
            return {
                "path": file_path,
                "public_url": public_url
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao fazer upload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao fazer upload do arquivo: {str(e)}"
            )
    
    async def upload_multiple_files(
        self,
        files: List[UploadFile],
        user_id: int,
        category: str,
        allowed_types: str = 'all'
    ) -> List[Dict[str, str]]:
        """
        Faz upload de múltiplos arquivos
        
        Args:
            files: Lista de arquivos
            user_id: ID do usuário
            category: Categoria dos arquivos
            allowed_types: Tipos permitidos
            
        Returns:
            Lista de dicts com path e public_url
        """
        results = []
        
        for file in files:
            try:
                result = await self.upload_file(file, user_id, category, allowed_types)
                results.append(result)
            except HTTPException as e:
                logger.warning(f"Erro ao fazer upload de {file.filename}: {e.detail}")
                # Continua com os próximos arquivos
        
        return results
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Remove arquivo do storage
        
        Args:
            file_path: Caminho do arquivo no storage
            
        Returns:
            bool: True se removido com sucesso
        """
        try:
            self.storage.from_(self.BUCKET_NAME).remove([file_path])
            logger.info(f"Arquivo removido: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao remover arquivo {file_path}: {str(e)}")
            return False
    
    async def delete_multiple_files(self, file_paths: List[str]) -> int:
        """
        Remove múltiplos arquivos
        
        Args:
            file_paths: Lista de caminhos dos arquivos
            
        Returns:
            int: Número de arquivos removidos com sucesso
        """
        try:
            self.storage.from_(self.BUCKET_NAME).remove(file_paths)
            logger.info(f"{len(file_paths)} arquivos removidos")
            return len(file_paths)
        except Exception as e:
            logger.error(f"Erro ao remover arquivos: {str(e)}")
            return 0
    
    async def list_user_files(self, user_id: int, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista arquivos de um usuário
        
        Args:
            user_id: ID do usuário
            category: Categoria opcional para filtrar
            
        Returns:
            Lista de arquivos
        """
        try:
            path = f"{user_id}/{category}" if category else str(user_id)
            
            files = self.storage.from_(self.BUCKET_NAME).list(path)
            
            return [
                {
                    "name": f.get("name"),
                    "path": f"{path}/{f.get('name')}",
                    "size": f.get("metadata", {}).get("size"),
                    "created_at": f.get("created_at"),
                    "updated_at": f.get("updated_at")
                }
                for f in files
            ]
        except Exception as e:
            logger.error(f"Erro ao listar arquivos: {str(e)}")
            return []
    
    def get_public_url(self, file_path: str) -> str:
        """
        Obtém URL pública de um arquivo
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            str: URL pública
        """
        return self.storage.from_(self.BUCKET_NAME).get_public_url(file_path)
