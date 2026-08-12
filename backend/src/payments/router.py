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
from src.core.ownership import assert_owned, assert_owned_optional
from .calculo import calcular_pagamento
from .repository import PaymentRepository
from .schema import (
    PaymentCreate,
    PaymentResponse,
    PaymentUpdate,
    PaymentCreateInternal,
    PaymentCalculateRequest,
    PaymentRegisterRequest,
    BulkConfirmRequest,
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

    calc = calcular_pagamento(
        aluguel=contract.rent,
        taxa_multa=contract.fine_rate,
        taxa_juros=contract.interest_rate,
        vencimento=data.due_date,
        data_pagamento=data.payment_date,
        valor_pago=data.paid_amount,
    )

    return {
        "base_amount": calc.base,
        "fine_amount": calc.multa,
        "interest_amount": calc.juros,
        "total_addition": calc.acrescimo,
        "total_expected": calc.total_devido,
        "days_overdue": calc.dias_atraso,
        "status": calc.situacao,
        "paid_amount": calc.pago,
        "remaining_amount": calc.restante,
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

    calc = calcular_pagamento(
        aluguel=contract.rent,
        taxa_multa=contract.fine_rate,
        taxa_juros=contract.interest_rate,
        vencimento=data.due_date,
        data_pagamento=data.payment_date,
        valor_pago=data.paid_amount,
    )

    # Quando informados explicitamente, property_id/tenant_id são do cliente e
    # precisam ser validados. Quando omitidos, herdam do contrato — que já foi
    # verificado como pertencente ao usuário logo acima.
    from src.properties.models import Property
    from src.tenants.models import Tenant

    assert_owned_optional(db, Property, data.property_id, user_id)
    assert_owned_optional(db, Tenant, data.tenant_id, user_id)

    property_id = data.property_id or contract.property_id
    tenant_id = data.tenant_id or contract.tenant_id

    internal = PaymentCreateInternal(
        user_id=user_id,
        property_id=property_id,
        tenant_id=tenant_id,
        contract_id=data.contract_id,
        due_date=data.due_date,
        payment_date=data.payment_date,
        amount=calc.base,
        # Multa e juros em colunas separadas: somados num campo só, a
        # composição da cobrança ficava impossível de auditar.
        fine_amount=calc.multa,
        interest_amount=calc.juros,
        total_amount=calc.pago,
        status=calc.situacao,
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
    data: BulkConfirmRequest,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
    repository: PaymentRepository = Depends(get_payment_repository),
):
    """
    Confirmar múltiplos pagamentos — tudo ou nada.

    Antes era um commit por item dentro do laço: uma falha no meio deixava o
    lote parcialmente aplicado e a resposta era 200, omitindo silenciosamente
    o que não foi confirmado. Agora é uma transação só, e ids inexistentes (ou
    de outro usuário) fazem a operação inteira falhar com 404 em vez de serem
    ignorados sem aviso.
    """
    payment_date = data.payment_date or date.today()

    try:
        confirmed = []
        nao_encontrados = []
        for pid in data.payment_ids:
            updated = repository.update(
                pid, user_id,
                PaymentUpdate(payment_date=payment_date, status="pago"),
                commit=False,
            )
            if updated:
                confirmed.append(updated)
            else:
                nao_encontrados.append(pid)

        if nao_encontrados:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pagamentos não encontrados: {nao_encontrados}",
            )

        db.commit()
    except Exception:
        db.rollback()
        raise

    for pagamento in confirmed:
        db.refresh(pagamento)
    return confirmed


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment_data: PaymentCreate,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
    repository: PaymentRepository = Depends(get_payment_repository),
):
    """Criar novo pagamento"""
    from src.contracts.models import Contract
    from src.properties.models import Property
    from src.tenants.models import Tenant

    # As FKs vêm do cliente: valide a posse antes de gravar (guarda anti-IDOR).
    assert_owned(db, Property, payment_data.property_id, user_id)
    assert_owned(db, Tenant, payment_data.tenant_id, user_id)
    assert_owned(db, Contract, payment_data.contract_id, user_id)

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

