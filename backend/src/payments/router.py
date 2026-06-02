"""
Router para o módulo de pagamentos
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.security import get_current_user_local_id
from .repository import PaymentRepository
from .schema import (
    PaymentCreate,
    PaymentResponse,
    PaymentUpdate,
    PaymentCreateInternal,
    PaymentCalculateRequest,
    PaymentRegisterRequest,
)

router = APIRouter()


def get_payment_repository(db: Session = Depends(get_db)) -> PaymentRepository:
    """Dependency para obter repository de pagamentos"""
    return PaymentRepository(db)


@router.get("/", response_model=List[PaymentResponse])
def get_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    property_id: Optional[int] = Query(None, description="Filtrar por propriedade"),
    tenant_id: Optional[int] = Query(None, description="Filtrar por inquilino"),
    user_id: int = Depends(get_current_user_local_id),
    repository: PaymentRepository = Depends(get_payment_repository),
):
    """Listar pagamentos com filtros opcionais"""

    if property_id:
        payments = repository.get_by_property(user_id, property_id)
    elif tenant_id:
        payments = repository.get_by_tenant(user_id, tenant_id)
    elif status:
        payments = repository.get_by_status(user_id, status)
    else:
        payments = repository.get_by_user(user_id, skip, limit)
    
    return payments


# ---------------------------------------------------------------------------
# Static routes — MUST come before /{payment_id} to avoid Starlette 405
# ---------------------------------------------------------------------------

@router.post("/calculate")
def calculate_payment(
    data: PaymentCalculateRequest,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
):
    """Calcular multa e juros com base nas taxas do contrato"""
    from src.contracts.models import Contract

    contract = db.query(Contract).filter(
        Contract.id == data.contract_id, Contract.user_id == user_id
    ).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")

    rent = float(contract.rent)
    fine_rate = float(contract.fine_rate or 0)
    interest_rate = float(contract.interest_rate or 0)

    payment_dt = data.payment_date or date.today()
    days_overdue = max(0, (payment_dt - data.due_date).days)

    fine_amount = 0.0
    interest_amount = 0.0
    if days_overdue > 0:
        fine_amount = rent * fine_rate / 100
        interest_amount = rent * (interest_rate / 100) * (days_overdue / 30)

    total_addition = fine_amount + interest_amount
    total_expected = rent + total_addition
    paid = float(data.paid_amount or 0)
    remaining = max(0.0, total_expected - paid)

    if paid >= total_expected and paid > 0:
        calc_status = "pago"
    elif paid > 0:
        calc_status = "parcial"
    elif days_overdue > 0:
        calc_status = "atrasado"
    else:
        calc_status = "pendente"

    return {
        "base_amount": round(rent, 2),
        "fine_amount": round(fine_amount, 2),
        "interest_amount": round(interest_amount, 2),
        "total_addition": round(total_addition, 2),
        "total_expected": round(total_expected, 2),
        "days_overdue": days_overdue,
        "status": calc_status,
        "paid_amount": round(paid, 2),
        "remaining_amount": round(remaining, 2),
    }


@router.post("/register", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def register_payment(
    data: PaymentRegisterRequest,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
    repository: PaymentRepository = Depends(get_payment_repository),
):
    """Registrar pagamento com cálculo automático de multa e juros"""
    from src.contracts.models import Contract

    contract = db.query(Contract).filter(
        Contract.id == data.contract_id, Contract.user_id == user_id
    ).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")

    rent = float(contract.rent)
    fine_rate = float(contract.fine_rate or 0)
    interest_rate = float(contract.interest_rate or 0)
    paid = float(data.paid_amount)

    days_overdue = max(0, (data.payment_date - data.due_date).days)
    fine_amount = 0.0
    interest_amount = 0.0
    if days_overdue > 0:
        fine_amount = rent * fine_rate / 100
        interest_amount = rent * (interest_rate / 100) * (days_overdue / 30)

    total_expected = rent + fine_amount + interest_amount

    if paid >= total_expected and paid > 0:
        pay_status = "pago"
    elif paid > 0:
        pay_status = "parcial"
    elif days_overdue > 0:
        pay_status = "atrasado"
    else:
        pay_status = "pendente"

    property_id = data.property_id or contract.property_id
    tenant_id = data.tenant_id or contract.tenant_id

    internal = PaymentCreateInternal(
        user_id=user_id,
        property_id=property_id,
        tenant_id=tenant_id,
        contract_id=data.contract_id,
        due_date=data.due_date,
        payment_date=data.payment_date,
        amount=Decimal(str(round(rent, 2))),
        fine_amount=Decimal(str(round(fine_amount + interest_amount, 2))),
        total_amount=Decimal(str(round(paid, 2))),
        status=pay_status,
        payment_method=data.payment_method,
        description=data.description,
    )
    new_payment = repository.create(internal)

    return new_payment


@router.get("/overdue/list", response_model=List[PaymentResponse])
def get_overdue_payments(
    user_id: int = Depends(get_current_user_local_id),
    repository: PaymentRepository = Depends(get_payment_repository),
):
    """Listar pagamentos em atraso"""
    return repository.get_overdue_payments(user_id)


@router.post("/bulk-confirm/", response_model=List[PaymentResponse])
def bulk_confirm_payments(
    data: dict,
    user_id: int = Depends(get_current_user_local_id),
    repository: PaymentRepository = Depends(get_payment_repository),
):
    """Confirmar múltiplos pagamentos"""
    payment_ids: List[int] = data.get("payment_ids", [])
    payment_date_str: Optional[str] = data.get("payment_date")
    payment_date = date.fromisoformat(payment_date_str) if payment_date_str else date.today()

    confirmed = []
    for pid in payment_ids:
        updated = repository.update(
            pid, user_id,
            PaymentUpdate(payment_date=payment_date, status="pago")
        )
        if updated:
            confirmed.append(updated)
    return confirmed


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment_data: PaymentCreate,
    user_id: int = Depends(get_current_user_local_id),
    repository: PaymentRepository = Depends(get_payment_repository),
):
    """Criar novo pagamento"""

    payment_create_internal = PaymentCreateInternal(
        **payment_data.dict(exclude={'user_id'}),
        user_id=user_id
    )
    
    new_payment = repository.create(payment_create_internal)
    return new_payment


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repository: PaymentRepository = Depends(get_payment_repository),
):
    """Obter pagamento por ID"""

    payment = repository.get_by_id_and_user(payment_id, user_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento não encontrado"
        )
    return payment


@router.put("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    user_id: int = Depends(get_current_user_local_id),
    repository: PaymentRepository = Depends(get_payment_repository),
):
    """Atualizar pagamento"""

    updated_payment = repository.update(payment_id, user_id, payment_data)
    if not updated_payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento não encontrado"
        )
    return updated_payment


@router.delete("/{payment_id}")
def delete_payment(
    payment_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repository: PaymentRepository = Depends(get_payment_repository),
):
    """Deletar pagamento"""

    success = repository.delete(payment_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento não encontrado"
        )
    return {"message": "Pagamento deletado com sucesso"}


@router.post("/{payment_id}/confirm/", response_model=PaymentResponse)
def confirm_payment(
    payment_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repository: PaymentRepository = Depends(get_payment_repository),
):
    """Marcar pagamento como pago"""
    updated = repository.update(
        payment_id, user_id,
        PaymentUpdate(payment_date=date.today(), status="pago"),
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento não encontrado",
        )
    return updated

