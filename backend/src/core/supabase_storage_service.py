"""
Serviço para gerenciamento de arquivos no Supabase Storage
"""

from typing import Optional, List, Dict, Any
from fastapi import UploadFile, HTTPException, status
from supabase import Client
import logging
import os
import re
import uuid
from datetime import datetime
import mimetypes

logger = logging.getLogger(__name__)


class SupabaseStorageService:
    """Serviço para upload e gerenciamento de arquivos no Supabase Storage"""
    
    BUCKET_NAME = "users"
    # `.svg` foi REMOVIDO das imagens: SVG é um documento XML que pode conter
    # <script>, e servido do domínio público do Supabase vira XSS armazenado.
    ALLOWED_EXTENSIONS = {
        'images': {'.jpg', '.jpeg', '.png', '.gif', '.webp'},
        'documents': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt'},
        'all': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.doc', '.docx',
                '.xls', '.xlsx', '.txt'}
    }

    # Assinaturas (magic bytes) dos formatos cujo conteúdo dá para verificar.
    # A extensão é escolhida por quem envia, então sozinha não prova nada:
    # um executável renomeado para .png passava direto.
    _ASSINATURAS = {
        b"\xff\xd8\xff": "image/jpeg",
        b"\x89PNG\r\n\x1a\n": "image/png",
        b"GIF87a": "image/gif",
        b"GIF89a": "image/gif",
        b"%PDF-": "application/pdf",
    }
    _TAMANHO_CABECALHO = 12

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    # Só letras, números, ponto, hífen e underscore sobrevivem no nome final.
    _CARACTERES_INSEGUROS = re.compile(r"[^A-Za-z0-9._-]")

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.storage = supabase_client.storage

    def _validate_file(self, file: UploadFile, allowed_types: str = 'all') -> None:
        """
        Valida extensão, tamanho e — para os formatos conhecidos — o CONTEÚDO.

        Raises:
            HTTPException: Se arquivo inválido
        """
        file_ext = os.path.splitext(file.filename or '')[1].lower()
        allowed_exts = self.ALLOWED_EXTENSIONS.get(allowed_types, self.ALLOWED_EXTENSIONS['all'])

        if file_ext not in allowed_exts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de arquivo não permitido. Extensões aceitas: {', '.join(sorted(allowed_exts))}"
            )

        # Verifica tamanho (se possível)
        if hasattr(file.file, 'seek') and hasattr(file.file, 'tell'):
            file.file.seek(0, 2)  # Move para o final
            file_size = file.file.tell()
            file.file.seek(0)  # Volta para o início

            if file_size == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Arquivo vazio."
                )

            if file_size > self.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Arquivo muito grande. Tamanho máximo: {self.MAX_FILE_SIZE / (1024*1024):.1f}MB"
                )

        self._validar_conteudo(file, file_ext)

    def _validar_conteudo(self, file: UploadFile, extensao: str) -> None:
        """
        Confere que os primeiros bytes correspondem à extensão declarada.

        Formatos sem assinatura estável (.txt, .doc, .xls) passam — para eles a
        verificação seria heurística e daria falso negativo em arquivo legítimo.
        Os formatos que importam para XSS/execução (imagens e PDF) são checados.
        """
        if not hasattr(file.file, "read"):
            return

        cabecalho = file.file.read(self._TAMANHO_CABECALHO)
        file.file.seek(0)
        if not cabecalho:
            return

        detectado = next(
            (mime for assinatura, mime in self._ASSINATURAS.items()
             if cabecalho.startswith(assinatura)),
            None,
        )

        esperados = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
            ".gif": "image/gif", ".pdf": "application/pdf",
        }
        esperado = esperados.get(extensao)
        if esperado is None:
            return  # extensão sem assinatura verificável

        if detectado != esperado:
            logger.warning(
                "Conteúdo incompatível com a extensão: %s declarava %s, detectado %s",
                file.filename, esperado, detectado or "desconhecido",
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O conteúdo do arquivo não corresponde à extensão informada.",
            )

    def _sanitizar_nome(self, filename: str) -> str:
        """
        Reduz o nome a um componente seguro.

        `os.path.basename` neutraliza `../` e caminhos absolutos: antes o nome
        só trocava espaço por underscore, então um nome malicioso conseguia
        escrever fora do prefixo `{user_id}/` — cruzando a fronteira entre
        clientes no storage.
        """
        base = os.path.basename(filename or "arquivo")
        seguro = self._CARACTERES_INSEGUROS.sub("_", base).lstrip(".")
        return (seguro or "arquivo")[:100]

    def _generate_file_path(self, user_id: int, category: str, filename: str) -> str:
        """
        Gera caminho único no formato {user_id}/{category}/{timestamp}_{nome}.

        O sufixo aleatório evita colisão entre uploads no mesmo segundo — o
        timestamp sozinho fazia dois arquivos simultâneos se sobrescreverem
        (o upload usa upsert=true).
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sufixo = uuid.uuid4().hex[:8]
        return f"{user_id}/{category}/{timestamp}_{sufixo}_{self._sanitizar_nome(filename)}"
    
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

            # Content-type derivado da EXTENSÃO já validada, não do cabeçalho
            # enviado pelo cliente: o valor do cliente é arbitrário e é ele que
            # o navegador respeita ao servir o arquivo — `text/html` num
            # arquivo público vira XSS armazenado.
            extensao = os.path.splitext(file.filename or "")[1].lower()
            content_type = (
                mimetypes.guess_type(f"x{extensao}")[0] or "application/octet-stream"
            )

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
            # Registra o detalhe no log, mas não o devolve ao cliente: a
            # mensagem do storage pode expor nome de bucket e caminho interno.
            logger.exception("Erro ao fazer upload de %s", file.filename)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Não foi possível enviar o arquivo. Tente novamente."
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

        Raises:
            HTTPException 400: se algum arquivo for rejeitado.

        Antes as falhas eram engolidas e a resposta era 200 "enviados com
        sucesso" listando só os que passaram — quem enviou 5 imagens e teve 2
        rejeitadas não era informado. Falhar por inteiro deixa o resultado
        previsível: ou tudo entrou, ou o cliente sabe o que corrigir.
        """
        results = []
        rejeitados = []

        for file in files:
            try:
                result = await self.upload_file(file, user_id, category, allowed_types)
                results.append(result)
            except HTTPException as e:
                logger.warning("Upload rejeitado (%s): %s", file.filename, e.detail)
                rejeitados.append(f"{file.filename}: {e.detail}")

        if rejeitados:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhum arquivo foi enviado. " + " | ".join(rejeitados),
            )

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
