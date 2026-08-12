"""
Router para o módulo de propriedades
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, UploadFile, File
from sqlalchemy.orm import Session

from src.database import get_db
from src.security import get_current_user_local_id, get_storage_service
from src.core.integrity import traduzir_erros_de_integridade
from src.core.ownership import assert_owned_optional
from src.core.supabase_storage_service import SupabaseStorageService
from .repository import PropertyRepository
from .schema import PropertyCreate, PropertyResponse, PropertyUpdate, PropertyCreateInternal

router = APIRouter()


def get_property_repository(db: Session = Depends(get_db)) -> PropertyRepository:
    """Dependency para obter repository de propriedades"""
    return PropertyRepository(db)


@router.get("/", response_model=List[PropertyResponse])
def get_properties(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    property_type: Optional[str] = Query(None, description="Filtrar por tipo de propriedade"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    min_rent: Optional[float] = Query(None, ge=0, description="Valor mínimo do aluguel"),
    max_rent: Optional[float] = Query(None, ge=0, description="Valor máximo do aluguel"),
    min_area: Optional[float] = Query(None, ge=0, description="Área mínima"),
    max_area: Optional[float] = Query(None, ge=0, description="Área máxima"),
    user_id: int = Depends(get_current_user_local_id),
    repository: PropertyRepository = Depends(get_property_repository),
):
    """Listar propriedades com filtros opcionais"""
    
    properties = repository.search_properties(
        user_id=user_id,
        skip=skip,
        limit=limit,
        property_type=property_type,
        status=status,
        min_rent=min_rent,
        max_rent=max_rent,
        min_area=min_area,
        max_area=max_area,
    )
    return properties


@router.get("/available", response_model=List[PropertyResponse])
def get_available_properties(
    user_id: int = Depends(get_current_user_local_id),
    repository: PropertyRepository = Depends(get_property_repository)
):
    """Listar apenas propriedades disponíveis (vacant)"""
    properties = repository.get_vacant_properties(user_id)
    return properties


@router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
def create_property(
    property_data: PropertyCreate,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
    repository: PropertyRepository = Depends(get_property_repository),
):
    """Criar nova propriedade"""
    from src.tenants.models import Tenant

    # tenant_id é opcional e vem do cliente: impede vincular inquilino alheio.
    assert_owned_optional(db, Tenant, property_data.tenant_id, user_id)

    # Criar schema interno com user_id
    property_create_internal = PropertyCreateInternal(
        **property_data.dict(exclude={'user_id'}),
        user_id=user_id
    )
    
    new_property = repository.create(property_create_internal)
    return new_property


@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(
    property_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repository: PropertyRepository = Depends(get_property_repository),
):
    """Obter propriedade por ID"""

    property_obj = repository.get_by_id_and_user(property_id, user_id)
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propriedade não encontrada"
        )
    return property_obj


@router.put("/{property_id}", response_model=PropertyResponse)
def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
    repository: PropertyRepository = Depends(get_property_repository),
):
    """Atualizar propriedade"""
    from src.tenants.models import Tenant

    assert_owned_optional(db, Tenant, property_data.tenant_id, user_id)

    updated_property = repository.update(property_id, user_id, property_data)
    if not updated_property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propriedade não encontrada"
        )
    return updated_property


@router.delete("/{property_id}")
def delete_property(
    property_id: int,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
    repository: PropertyRepository = Depends(get_property_repository),
):
    """
    Deletar propriedade.

    Contratos, pagamentos e despesas do imóvel são removidos em cascata
    (política definida na revisão 0006).
    """

    with traduzir_erros_de_integridade(
        db,
        conflito_fk="Imóvel não pode ser removido: existem dados vinculados a ele.",
    ):
        success = repository.delete(property_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propriedade não encontrada"
        )
    return {"message": "Propriedade deletada com sucesso"}


@router.get("/statistics/summary")
def get_property_statistics(
    user_id: int = Depends(get_current_user_local_id),
    repository: PropertyRepository = Depends(get_property_repository),
):
    """Obter estatísticas das propriedades — uma única consulta GROUP BY"""

    counts = repository.count_by_status(user_id)
    total = sum(counts.values())
    occupied = counts.get("occupied", 0)
    vacant = counts.get("vacant", 0)
    maintenance = counts.get("maintenance", 0)

    return {
        "total": total,
        "vacant": vacant,
        "occupied": occupied,
        "maintenance": maintenance,
        "occupancy_rate": (occupied / total * 100) if total > 0 else 0
    }


@router.post("/{property_id}/images", response_model=dict)
async def upload_property_images(
    property_id: int,
    images: List[UploadFile] = File(...),
    user_id: int = Depends(get_current_user_local_id),
    repository: PropertyRepository = Depends(get_property_repository),
    storage_service: SupabaseStorageService = Depends(get_storage_service),
):
    """
    Upload de imagens para uma propriedade
    
    As imagens são enviadas para o Supabase Storage no bucket 'users'
    com a estrutura: {user_id}/properties/{timestamp}_{filename}
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"📸 Iniciando upload de {len(images)} imagens para propriedade {property_id}")
    
    # Verifica se a propriedade existe e pertence ao usuário
    property_obj = repository.get_by_id_and_user(property_id, user_id)
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propriedade não encontrada"
        )
    
    # Faz upload das imagens
    uploaded_files = await storage_service.upload_multiple_files(
        files=images,
        user_id=user_id,
        category="properties",
        allowed_types="images"
    )
    
    if not uploaded_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma imagem foi enviada com sucesso"
        )
    
    logger.info(f"✅ Upload concluído. Arquivos enviados: {len(uploaded_files)}")
    
    # Atualiza a propriedade com as URLs das imagens
    current_images = property_obj.images or []
    new_image_urls = [file["public_url"] for file in uploaded_files]
    updated_images = current_images + new_image_urls
    
    logger.info(f"🔗 URLs das imagens: {new_image_urls}")
    
    update_data = PropertyUpdate(images=updated_images)
    updated_property = repository.update(property_id, user_id, update_data)
    
    logger.info(f"💾 Propriedade atualizada com {len(updated_images)} imagens no total")
    
    return {
        "message": f"{len(uploaded_files)} imagens enviadas com sucesso",
        "images": new_image_urls,
        "property": updated_property
    }


@router.delete("/{property_id}/images/{image_index}")
async def delete_property_image(
    property_id: int,
    # `ge=0`: só o limite superior era checado, então índice negativo passava
    # e `images[-1]` apagava a ÚLTIMA imagem, não a pedida — incluindo o
    # arquivo no storage.
    image_index: int = Path(..., ge=0),
    user_id: int = Depends(get_current_user_local_id),
    repository: PropertyRepository = Depends(get_property_repository),
    storage_service: SupabaseStorageService = Depends(get_storage_service),
):
    """
    Remove uma imagem específica de uma propriedade
    """
    # Verifica se a propriedade existe
    property_obj = repository.get_by_id_and_user(property_id, user_id)
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propriedade não encontrada"
        )
    
    if not property_obj.images or image_index >= len(property_obj.images):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagem não encontrada"
        )
    
    # Remove a imagem do storage
    image_url = property_obj.images[image_index]
    # Extrai o path da URL pública
    if "/storage/v1/object/public/users/" in image_url:
        file_path = image_url.split("/storage/v1/object/public/users/")[1]
        await storage_service.delete_file(file_path)
    
    # Atualiza a lista de imagens
    updated_images = [img for i, img in enumerate(property_obj.images) if i != image_index]
    update_data = PropertyUpdate(images=updated_images)
    updated_property = repository.update(property_id, user_id, update_data)
    
    return {
        "message": "Imagem removida com sucesso",
        "property": updated_property
    }

