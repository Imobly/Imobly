from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_id_from_token
from app.db.session import get_db

from .controller import contract_controller
from .schemas import ContractCreate, ContractResponse, ContractUpdate

router = APIRouter()


@router.post("/", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract: ContractCreate,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Criar novo contrato"""
    return contract_controller(db).create_contract(db, user_id, contract)


@router.get("/", response_model=List[ContractResponse])
async def list_contracts(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(
        None, description="Filtrar por status: active, expired, terminated"
    ),
    property_id: Optional[int] = Query(None, description="Filtrar por propriedade"),
    tenant_id: Optional[int] = Query(None, description="Filtrar por inquilino"),
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Listar contratos do usuário autenticado"""
    return contract_controller(db).get_contracts(
        db,
        user_id,
        skip=skip,
        limit=limit,
        status=status,
        property_id=property_id,
        tenant_id=tenant_id,
    )


@router.get("/active", response_model=List[ContractResponse])
async def list_active_contracts(
    user_id: int = Depends(get_current_user_id_from_token), db: Session = Depends(get_db)
):
    """Listar apenas contratos ativos"""
    return contract_controller(db).get_active_contracts(db, user_id)


@router.get("/expiring", response_model=List[ContractResponse])
async def list_expiring_contracts(
    days_ahead: int = Query(30, description="Dias à frente para verificar vencimento"),
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Listar contratos que vencem em breve"""
    return contract_controller(db).get_expiring_contracts(db, user_id, days_ahead)


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: int,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Obter contrato por ID"""
    return contract_controller(db).get_contract_by_id(db, contract_id, user_id)


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int,
    contract_update: ContractUpdate,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Atualizar contrato"""
    return contract_controller(db).update_contract(db, contract_id, user_id, contract_update)


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: int,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Deletar contrato"""
    return contract_controller(db).delete_contract(db, contract_id, user_id)


@router.patch("/{contract_id}/renew", response_model=ContractResponse)
async def renew_contract(
    contract_id: int,
    new_end_date: str = Query(..., description="Nova data de término (YYYY-MM-DD)"),
    new_rent: Optional[float] = Query(None, description="Novo valor do aluguel"),
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Renovar contrato"""
    from datetime import datetime

    end_date = datetime.strptime(new_end_date, "%Y-%m-%d").date()
    return contract_controller(db).renew_contract(db, contract_id, user_id, end_date, new_rent)


@router.patch("/{contract_id}/status", response_model=ContractResponse)
async def update_contract_status(
    contract_id: int,
    new_status: str = Query(..., description="Novo status: active, expired, terminated"),
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Atualizar status do contrato"""
    from fastapi import HTTPException

    valid_statuses = ["active", "expired", "terminated"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"Status inválido. Use: {', '.join(valid_statuses)}"
        )

    contract_obj = contract_controller(db).repository.update_status(
        db, contract_id, user_id, new_status
    )
    if not contract_obj:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    return contract_obj
