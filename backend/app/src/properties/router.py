from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_id_from_token
from app.core.upload_service import upload_service
from app.db.session import get_db

from .controller import property_controller
from .schemas import PropertyCreate, PropertyResponse, PropertyUpdate

router = APIRouter()


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
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Listar propriedades com filtros opcionais"""
    properties = property_controller(db).get_properties(
        db=db,
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
    user_id: int = Depends(get_current_user_id_from_token), db: Session = Depends(get_db)
):
    """Listar apenas propriedades disponíveis"""
    properties = property_controller(db).get_available_properties(db, user_id)
    return properties


@router.post("/", response_model=PropertyResponse, status_code=201)
def create_property(
    property: PropertyCreate,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Criar nova propriedade"""
    new_property = property_controller(db).create_property(
        db=db, user_id=user_id, property_data=property
    )
    return new_property


@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(
    property_id: int,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Obter propriedade por ID"""
    property_obj = property_controller(db).get_property_by_id(
        db, property_id=property_id, user_id=user_id
    )
    return property_obj


@router.put("/{property_id}", response_model=PropertyResponse)
def update_property(
    property_id: int,
    property: PropertyUpdate,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Atualizar propriedade"""
    updated_property = property_controller(db).update_property(
        db, property_id=property_id, user_id=user_id, property_data=property
    )
    return updated_property


@router.patch("/{property_id}/status", response_model=PropertyResponse)
def update_property_status(
    property_id: int,
    status: str = Query(..., description="Novo status da propriedade"),
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Atualizar apenas o status da propriedade"""
    updated_property = property_controller(db).update_property_status(
        db, property_id=property_id, user_id=user_id, status=status
    )
    return updated_property


@router.delete("/{property_id}")
def delete_property(
    property_id: int,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Deletar propriedade"""
    property_controller(db).delete_property(db, property_id=property_id, user_id=user_id)
    return {"message": "Propriedade deletada com sucesso"}


# ==================== UPLOAD ENDPOINTS ====================


@router.post("/{property_id}/upload-images", status_code=status.HTTP_201_CREATED)
async def upload_property_images(
    property_id: int,
    files: List[UploadFile] = File(..., description="Imagens da propriedade (max 10 arquivos)"),
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    Upload de múltiplas imagens para uma propriedade

    - Aceita até 10 imagens por requisição
    - Formatos permitidos: JPG, JPEG, PNG, GIF, WEBP
    - Tamanho máximo por arquivo: 10MB
    """
    # Verificar se a propriedade existe e pertence ao usuário
    property_obj = property_controller(db).get_property_by_id(db, property_id, user_id)

    # Salvar arquivos
    uploaded_files = await upload_service.save_multiple_files(
        files=files, folder=f"properties/{property_id}", allowed_types="image", max_files=10
    )

    # Extrair apenas as URLs dos arquivos
    new_image_urls = [file_info["url"] for file_info in uploaded_files]

    # Atualizar propriedade com novas imagens
    current_images = property_obj.images or []
    updated_images = current_images + new_image_urls

    property_controller(db).update_property(
        db,
        property_id=property_id,
        user_id=user_id,
        property_data=PropertyUpdate(images=updated_images),
    )

    return {
        "message": f"{len(uploaded_files)} imagens enviadas com sucesso",
        "uploaded_files": uploaded_files,
        "total_images": len(updated_images),
    }


@router.delete("/{property_id}/images")
async def delete_property_image(
    property_id: int,
    image_url: str = Query(..., description="URL da imagem a ser deletada"),
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    Deletar uma imagem específica da propriedade

    - Remove o arquivo do servidor
    - Atualiza o array de imagens no banco de dados
    """
    # Verificar se a propriedade existe e pertence ao usuário
    property_obj = property_controller(db).get_property_by_id(db, property_id, user_id)

    # Verificar se a imagem existe no array
    current_images = property_obj.images or []
    if image_url not in current_images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Imagem não encontrada na propriedade"
        )

    # Deletar arquivo físico
    deleted = upload_service.delete_file(image_url)

    # Remover URL do array
    updated_images = [img for img in current_images if img != image_url]

    property_controller(db).update_property(
        db,
        property_id=property_id,
        user_id=user_id,
        property_data=PropertyUpdate(images=updated_images),
    )

    return {
        "message": "Imagem deletada com sucesso",
        "file_deleted": deleted,
        "remaining_images": len(updated_images),
    }
