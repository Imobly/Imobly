"""
Router para o módulo de contratos
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.security import get_current_user_local_id
from .repository import ContractRepository
from .schema import ContractCreate, ContractCreateInternal, ContractResponse, ContractUpdate

router = APIRouter()


def get_contract_repository(db: Session = Depends(get_db)) -> ContractRepository:
    return ContractRepository(db)


# ------------------------------------------------------------------
# GET /  — listar contratos
# ------------------------------------------------------------------
@router.get("/", response_model=List[ContractResponse])
def get_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    tenant_id: Optional[int] = Query(None),
    property_id: Optional[int] = Query(None),
    user_id: int = Depends(get_current_user_local_id),
    repo: ContractRepository = Depends(get_contract_repository),
):
    """Listar contratos com filtros opcionais"""
    if tenant_id:
        return repo.get_by_tenant(tenant_id, user_id)
    if property_id:
        return repo.get_by_property(property_id, user_id)
    if status:
        return repo.get_by_status(user_id, status)
    return repo.get_by_user(user_id, skip, limit)


# ------------------------------------------------------------------
# GET /active  — contratos ativos
# ------------------------------------------------------------------
@router.get("/active", response_model=List[ContractResponse])
def get_active_contracts(
    user_id: int = Depends(get_current_user_local_id),
    repo: ContractRepository = Depends(get_contract_repository),
):
    return repo.get_active(user_id)


# ------------------------------------------------------------------
# GET /expiring  — contratos próximos do vencimento
# ------------------------------------------------------------------
@router.get("/expiring", response_model=List[ContractResponse])
def get_expiring_contracts(
    days_ahead: int = Query(30, ge=1, le=365),
    user_id: int = Depends(get_current_user_local_id),
    repo: ContractRepository = Depends(get_contract_repository),
):
    return repo.get_expiring(user_id, days_ahead)


# ------------------------------------------------------------------
# POST /  — criar contrato
# ------------------------------------------------------------------
@router.post("/", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract_data: ContractCreate,
    user_id: int = Depends(get_current_user_local_id),
    repo: ContractRepository = Depends(get_contract_repository),
    db: Session = Depends(get_db),
):
    """Criar novo contrato"""
    internal = ContractCreateInternal(
        **contract_data.dict(),
        user_id=user_id,
    )
    new_contract = repo.create(internal)

    # Auto-atualizar status do imóvel para 'occupied'
    if new_contract.status == "ativo":
        from src.properties.models import Property
        prop = db.query(Property).filter(Property.id == new_contract.property_id).first()
        if prop:
            prop.status = "occupied"
            prop.tenant_id = new_contract.tenant_id
            db.commit()

    return new_contract


# ------------------------------------------------------------------
# GET /{contract_id}  — obter contrato por ID
# ------------------------------------------------------------------
@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repo: ContractRepository = Depends(get_contract_repository),
):
    contract = repo.get_by_id_and_user(contract_id, user_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
    return contract


# ------------------------------------------------------------------
# PUT /{contract_id}  — atualizar contrato
# ------------------------------------------------------------------
@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    contract_data: ContractUpdate,
    user_id: int = Depends(get_current_user_local_id),
    repo: ContractRepository = Depends(get_contract_repository),
):
    updated = repo.update(contract_id, user_id, contract_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
    return updated


# ------------------------------------------------------------------
# PATCH /{contract_id}/status  — atualizar status
# ------------------------------------------------------------------
@router.patch("/{contract_id}/status", response_model=ContractResponse)
def update_contract_status(
    contract_id: int,
    new_status: str = Query(..., pattern="^(ativo|inativo|expirado)$"),
    user_id: int = Depends(get_current_user_local_id),
    repo: ContractRepository = Depends(get_contract_repository),
    db: Session = Depends(get_db),
):
    updated = repo.update_status(contract_id, user_id, new_status)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")

    # Auto-atualizar status do imóvel
    from src.properties.models import Property
    prop = db.query(Property).filter(Property.id == updated.property_id).first()
    if prop:
        if new_status == "ativo":
            prop.status = "occupied"
            prop.tenant_id = updated.tenant_id
        elif new_status in ("inativo", "expirado"):
            prop.status = "vacant"
            prop.tenant_id = None
        db.commit()

    return updated


# ------------------------------------------------------------------
# PATCH /{contract_id}/renew  — renovar contrato
# ------------------------------------------------------------------
@router.patch("/{contract_id}/renew", response_model=ContractResponse)
def renew_contract(
    contract_id: int,
    new_end_date: date = Query(...),
    new_rent: Optional[float] = Query(None),
    user_id: int = Depends(get_current_user_local_id),
    repo: ContractRepository = Depends(get_contract_repository),
):
    renewed = repo.renew(contract_id, user_id, new_end_date, new_rent)
    if not renewed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
    return renewed


# ------------------------------------------------------------------
# DELETE /{contract_id}  — deletar contrato
# ------------------------------------------------------------------
@router.delete("/{contract_id}", status_code=status.HTTP_200_OK)
def delete_contract(
    contract_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repo: ContractRepository = Depends(get_contract_repository),
    db: Session = Depends(get_db),
):
    # Buscar contrato antes de deletar para liberar imóvel
    from src.properties.models import Property
    contract = repo.get_by_id_and_user(contract_id, user_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")

    # Liberar imóvel
    prop = db.query(Property).filter(Property.id == contract.property_id).first()
    if prop and contract.status == "ativo":
        prop.status = "vacant"
        prop.tenant_id = None

    deleted = repo.delete(contract_id, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
    db.commit()
    return {"message": "Contrato deletado com sucesso"}
