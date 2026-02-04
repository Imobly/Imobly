from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_id_from_token
from app.core.upload_service import upload_service
from app.db.session import get_db

from .controller import tenant_controller
from .schemas import TenantCreate, TenantResponse, TenantUpdate

router = APIRouter()


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant: TenantCreate,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Criar novo inquilino"""
    return tenant_controller(db).create_tenant(db, user_id, tenant)


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Listar inquilinos"""
    return tenant_controller(db).get_tenants(db, user_id, skip=skip, limit=limit)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: int,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Obter inquilino por ID"""
    return tenant_controller(db).get_tenant_by_id(db, tenant_id, user_id)


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    tenant_update: TenantUpdate,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Atualizar inquilino"""
    return tenant_controller(db).update_tenant(db, tenant_id, user_id, tenant_update)


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: int,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Deletar inquilino"""
    return tenant_controller(db).delete_tenant(db, tenant_id, user_id)


# ==================== UPLOAD ENDPOINTS ====================


@router.post("/{tenant_id}/upload-documents", status_code=status.HTTP_201_CREATED)
async def upload_tenant_documents(
    tenant_id: int,
    files: List[UploadFile] = File(..., description="Documentos do inquilino (imagens ou PDFs)"),
    document_type: str = Query(
        ...,
        description="Tipo do documento",
        regex="^(rg|cpf|cnh|comprovante_residencia|comprovante_renda|contrato|outros)$",
    ),
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    Upload de documentos do inquilino

    - Aceita imagens (JPG, PNG) ou PDFs
    - Tamanho máximo por arquivo: 10MB
    - Tipos de documento: rg, cpf, cnh, comprovante_residencia, comprovante_renda, contrato, outros
    """
    # Verificar se o inquilino existe e pertence ao usuário
    tenant_obj = tenant_controller(db).get_tenant_by_id(db, tenant_id, user_id)

    # Salvar arquivos (permite imagens e documentos)
    uploaded_files = await upload_service.save_multiple_files(
        files=files, folder=f"tenants/{tenant_id}", allowed_types="all", max_files=5
    )

    # Preparar documentos para adicionar ao tenant
    current_documents = tenant_obj.documents or []

    for file_info in uploaded_files:
        document_entry = {
            "id": file_info["filename"].split(".")[0],  # Usar parte do nome como ID
            "name": file_info["original_filename"],
            "type": document_type,
            "url": file_info["url"],
            "file_type": file_info["type"],
            "size": file_info["size"],
            "uploaded_at": str(datetime.now()),
        }
        current_documents.append(document_entry)

    # Atualizar tenant com novos documentos
    tenant_controller(db).update_tenant(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        tenant_data=TenantUpdate(documents=current_documents),
    )

    return {
        "message": f"{len(uploaded_files)} documento(s) enviado(s) com sucesso",
        "uploaded_files": uploaded_files,
        "total_documents": len(current_documents),
    }


@router.delete("/{tenant_id}/documents")
async def delete_tenant_document(
    tenant_id: int,
    document_url: str = Query(..., description="URL do documento a ser deletado"),
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    Deletar um documento específico do inquilino

    - Remove o arquivo do servidor
    - Atualiza o array de documentos no banco de dados
    """
    # Verificar se o inquilino existe e pertence ao usuário
    tenant_obj = tenant_controller(db).get_tenant_by_id(db, tenant_id, user_id)

    # Verificar se o documento existe
    current_documents = tenant_obj.documents or []
    document_found = False
    updated_documents = []

    for doc in current_documents:
        if doc.get("url") == document_url:
            document_found = True
            # Deletar arquivo físico
            upload_service.delete_file(document_url)
        else:
            updated_documents.append(doc)

    if not document_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado"
        )

    # Atualizar tenant
    tenant_controller(db).update_tenant(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        tenant_data=TenantUpdate(documents=updated_documents),
    )

    return {
        "message": "Documento deletado com sucesso",
        "remaining_documents": len(updated_documents),
    }


@router.get("/{tenant_id}/documents")
async def list_tenant_documents(
    tenant_id: int,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    Listar todos os documentos de um inquilino
    """
    tenant_obj = tenant_controller(db).get_tenant_by_id(db, tenant_id, user_id)

    return {
        "tenant_id": tenant_id,
        "tenant_name": tenant_obj.name,
        "documents": tenant_obj.documents or [],
        "total_documents": len(tenant_obj.documents or []),
    }
