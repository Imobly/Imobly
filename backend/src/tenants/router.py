"""
Router para o módulo de inquilinos (tenants)
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database import get_db
from src.security import get_current_user_local_id, get_storage_service
from src.core.integrity import traduzir_erros_de_integridade
from src.core.ownership import assert_owned_optional
from src.core.supabase_storage_service import SupabaseStorageService
from .repository import TenantRepository
from .schema import TenantCreate, TenantResponse, TenantUpdate, TenantCreateInternal

logger = logging.getLogger(__name__)

router = APIRouter()


def get_tenant_repository(db: Session = Depends(get_db)) -> TenantRepository:
    """Dependency para obter repository de inquilinos"""
    return TenantRepository(db)


@router.get("/", response_model=List[TenantResponse])
def get_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Buscar por nome, email ou CPF"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    user_id: int = Depends(get_current_user_local_id),
    repository: TenantRepository = Depends(get_tenant_repository),
):
    """Listar inquilinos com filtros opcionais"""

    if search:
        tenants = repository.search_tenants(user_id, search, skip, limit)
    elif status == "ativo":
        tenants = repository.get_active_tenants(user_id)
    elif status == "inativo":
        tenants = repository.get_inactive_tenants(user_id)
    else:
        tenants = repository.get_by_user(user_id, skip, limit)

    return repository.anexar_status(tenants, user_id)


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    tenant_data: TenantCreate,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
    repository: TenantRepository = Depends(get_tenant_repository),
):
    """Criar novo inquilino"""
    from src.contracts.models import Contract

    # contract_id vem do cliente: impede vincular contrato de outro usuário.
    assert_owned_optional(db, Contract, tenant_data.contract_id, user_id)

    # Verificar se email já existe
    existing_tenant = repository.get_by_email(tenant_data.email, user_id)
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado para outro inquilino"
        )
    
    # Verificar se CPF já existe
    existing_cpf = repository.get_by_cpf(tenant_data.cpf_cnpj, user_id)
    if existing_cpf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF/CNPJ já cadastrado para outro inquilino"
        )
    
    # Criar schema interno com user_id
    data_dict = tenant_data.model_dump(exclude={'user_id'})
    tenant_create_internal = TenantCreateInternal(
        **data_dict,
        user_id=user_id,
    )

    # As checagens acima são "time-of-check/time-of-use": duas requisições
    # concorrentes passam ambas e uma estoura no INSERT. O banco é a única
    # fonte de verdade — traduzimos a violação em 409 em vez de 500.
    try:
        new_tenant = repository.create(tenant_create_internal)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um inquilino com este e-mail ou CPF/CNPJ",
        )
    return new_tenant


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repository: TenantRepository = Depends(get_tenant_repository),
):
    """Obter inquilino por ID"""

    tenant = repository.get_by_id_and_user(tenant_id, user_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inquilino não encontrado"
        )
    return repository.anexar_status([tenant], user_id)[0]


@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
    repository: TenantRepository = Depends(get_tenant_repository),
):
    """Atualizar inquilino"""
    from src.contracts.models import Contract

    assert_owned_optional(db, Contract, tenant_data.contract_id, user_id)

    # Verificar se email novo já existe (se fornecido)
    if tenant_data.email:
        existing_tenant = repository.get_by_email(tenant_data.email, user_id)
        if existing_tenant and existing_tenant.id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado para outro inquilino"
            )
    
    try:
        updated_tenant = repository.update(tenant_id, user_id, tenant_data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um inquilino com este e-mail ou CPF/CNPJ",
        )
    if not updated_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inquilino não encontrado"
        )
    return updated_tenant


@router.delete("/{tenant_id}")
def delete_tenant(
    tenant_id: int,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
    repository: TenantRepository = Depends(get_tenant_repository),
):
    """Deletar inquilino"""

    with traduzir_erros_de_integridade(
        db,
        conflito_fk=(
            "Inquilino não pode ser removido: existem contratos ou pagamentos "
            "vinculados a ele. Encerre-os antes de excluir."
        ),
    ):
        success = repository.delete(tenant_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inquilino não encontrado"
        )
    return {"message": "Inquilino deletado com sucesso"}


@router.get("/statistics/summary")
def get_tenant_statistics(
    user_id: int = Depends(get_current_user_local_id),
    repository: TenantRepository = Depends(get_tenant_repository),
):
    """Obter estatísticas dos inquilinos"""

    total = repository.count_by_user(user_id)
    active = repository.count_active_tenants(user_id)
    inactive = total - active
    
    return {
        "total": total,
        "active": active,
        "inactive": inactive,
    }


# ---------------------------------------------------------------------------
# Endpoints de documentos — Supabase Storage (bucket 'users', pasta 'tenants')
# ---------------------------------------------------------------------------

@router.get("/{tenant_id}/documents")
def get_tenant_documents(
    tenant_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repository: TenantRepository = Depends(get_tenant_repository),
):
    """Listar documentos do inquilino"""
    tenant = repository.get_by_id_and_user(tenant_id, user_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquilino não encontrado")
    documents = tenant.documents or []
    return {
        "tenant_id": tenant_id,
        "tenant_name": tenant.name,
        "documents": documents,
        "total_documents": len(documents),
    }


@router.post("/{tenant_id}/upload-documents")
async def upload_tenant_documents(
    tenant_id: int,
    document_type: str = Query(
        "outros",
        pattern="^(rg|cpf|cnh|comprovante_residencia|comprovante_renda|contrato|outros)$",
    ),
    files: List[UploadFile] = File(...),
    user_id: int = Depends(get_current_user_local_id),
    repository: TenantRepository = Depends(get_tenant_repository),
    storage: SupabaseStorageService = Depends(get_storage_service),
):
    """Upload de documentos para Supabase Storage (bucket 'users', pasta user_id/tenants/)"""
    tenant = repository.get_by_id_and_user(tenant_id, user_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquilino não encontrado")
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum arquivo enviado")

    uploaded = []
    current_docs: list = list(tenant.documents or [])

    for file in files:
        result = await storage.upload_file(file, user_id, "tenants", allowed_types="all")
        doc_entry = {
            "id": str(uuid.uuid4()),
            "name": file.filename or "documento",
            "type": document_type,
            "url": result["public_url"],
            "file_type": file.content_type or "application/octet-stream",
            "size": 0,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        current_docs.append(doc_entry)
        uploaded.append({
            "filename": result["path"].split("/")[-1],
            "original_filename": file.filename,
            "url": result["public_url"],
            "size": 0,
            "type": document_type,
        })

    repository.update(tenant_id, user_id, TenantUpdate(documents=current_docs))

    return {
        "message": f"{len(uploaded)} documento(s) enviado(s) com sucesso",
        "uploaded_files": uploaded,
        "total_documents": len(current_docs),
    }


@router.delete("/{tenant_id}/documents/")
async def delete_tenant_document(
    tenant_id: int,
    document_url: str = Query(..., description="URL pública do documento a remover"),
    user_id: int = Depends(get_current_user_local_id),
    repository: TenantRepository = Depends(get_tenant_repository),
    storage: SupabaseStorageService = Depends(get_storage_service),
):
    """Remove documento do Supabase Storage e do banco de dados"""
    tenant = repository.get_by_id_and_user(tenant_id, user_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquilino não encontrado")

    current_docs: list = list(tenant.documents or [])
    if not any(d.get("url") == document_url for d in current_docs):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado")

    # Delete from Supabase Storage: extract path after /storage/v1/object/public/users/
    file_deleted = False
    try:
        marker = "/storage/v1/object/public/users/"
        if marker in document_url:
            file_path = document_url.split(marker, 1)[1]
            file_deleted = await storage.delete_file(file_path)
    except Exception:
        # O registro sai do banco de qualquer forma — o vínculo é o que o
        # usuário enxerga. Mas o arquivo órfão precisa ficar rastreável: antes
        # era `except Exception: pass`, e o arquivo sumia do sistema sem
        # deixar registro de que continuava ocupando espaço no storage.
        logger.exception(
            "Documento removido do banco mas NÃO do storage (arquivo órfão): %s",
            document_url,
        )

    updated_docs = [d for d in current_docs if d.get("url") != document_url]
    repository.update(tenant_id, user_id, TenantUpdate(documents=updated_docs))

    return {
        "message": "Documento removido com sucesso",
        "file_deleted": file_deleted,
        "remaining_documents": len(updated_docs),
    }
