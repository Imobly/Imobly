"""
Router para o módulo de contratos
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database import get_db
from src.security import get_current_user_local_id
from src.core.integrity import traduzir_erros_de_integridade
from src.core.ownership import assert_owned, assert_owned_optional
from src.core.perf import marcar
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
    from src.properties.models import Property
    from src.tenants.models import Tenant

    marcar("autenticação + validação do payload (Pydantic)")

    # property_id/tenant_id vêm do cliente: sem esta guarda era possível criar
    # um contrato sobre o imóvel de outro usuário — e o bloco abaixo alterava
    # o status desse imóvel alheio.
    assert_owned(db, Property, contract_data.property_id, user_id)
    assert_owned(db, Tenant, contract_data.tenant_id, user_id)
    marcar("checagem de posse (imóvel + inquilino)")

    internal = ContractCreateInternal(
        **contract_data.model_dump(),
        user_id=user_id,
    )

    # Contrato e imóvel numa transação só: eram dois commits separados, e uma
    # falha entre eles deixava contrato ativo com o imóvel ainda 'vacant'.
    with traduzir_erros_de_integridade(
        db,
        conflito_exclusao=(
            "Já existe um contrato ativo para este imóvel no período informado."
        ),
    ):
        try:
            new_contract = repo.create(internal, commit=False)

            if new_contract.status == "ativo":
                prop = assert_owned(db, Property, new_contract.property_id, user_id)
                prop.status = "occupied"
                prop.tenant_id = new_contract.tenant_id

            db.commit()
            marcar("INSERT contrato + UPDATE imóvel + commit no Supabase")
        except IntegrityError:
            raise  # tratado pelo contexto acima (rollback incluído)
        except Exception:
            db.rollback()
            raise

    db.refresh(new_contract)
    marcar("refresh do contrato criado")
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
    db: Session = Depends(get_db),
    repo: ContractRepository = Depends(get_contract_repository),
):
    from src.properties.models import Property
    from src.tenants.models import Tenant

    # O update permite remanejar o contrato para outro imóvel/inquilino —
    # ambos precisam pertencer ao usuário.
    assert_owned_optional(db, Property, contract_data.property_id, user_id)
    assert_owned_optional(db, Tenant, contract_data.tenant_id, user_id)

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
    from src.properties.models import Property

    # Contrato e imóvel na MESMA transação (antes eram dois commits).
    try:
        updated = repo.update_status(contract_id, user_id, new_status, commit=False)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado"
            )

        # Filtrando por dono — era escrita cross-tenant: o imóvel era buscado
        # só por id.
        prop = assert_owned(db, Property, updated.property_id, user_id)
        if new_status == "ativo":
            prop.status = "occupied"
            prop.tenant_id = updated.tenant_id
        elif new_status in ("inativo", "expirado"):
            prop.status = "vacant"
            prop.tenant_id = None

        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(updated)
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

    try:
        # Liberar imóvel — filtrando por dono (era escrita cross-tenant).
        if contract.status == "ativo":
            prop = assert_owned(db, Property, contract.property_id, user_id)
            prop.status = "vacant"
            prop.tenant_id = None

        deleted = repo.delete(contract_id, user_id, commit=False)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado"
            )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Contrato deletado com sucesso"}
