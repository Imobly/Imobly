"""
Router de cobranças (`/api/v1/charges`).

Fonte da verdade da gestão de inquilinos e inadimplência. As rotas antigas de
`/api/v1/payments` continuam funcionando, mas hoje são um adaptador de leitura
e escrita sobre estas tabelas — não há mais dois lugares onde o mesmo dinheiro
é registrado.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.contracts.models import Contract
from src.core.ownership import assert_owned, assert_owned_optional
from src.core.tempo import hoje_brt
from src.database import get_db
from src.properties.models import Property
from src.security import get_current_user_local_id
from src.tenants.models import Tenant

from .calculo import CANCELADA, faixa_aging
from .geracao import gerar_cobrancas
from .models import Charge, PaymentEntry
from .repository import ChargeRepository
from .schema import (
    AgingBucket,
    AgingReport,
    ChargeCreate,
    ChargeDetail,
    ChargeListItem,
    ChargeRead,
    ChargePosition,
    ChargeUpdate,
    GenerateChargesRequest,
    GenerateChargesResponse,
    PaymentEntryCreate,
    PaymentEntryRead,
)

router = APIRouter()

ROTULOS_AGING = {
    "a_vencer": "A vencer",
    "d1_30": "1 a 30 dias",
    "d31_60": "31 a 60 dias",
    "d61_90": "61 a 90 dias",
    "d90_mais": "Mais de 90 dias",
}


def get_repository(db: Session = Depends(get_db)) -> ChargeRepository:
    return ChargeRepository(db)


def _posicao_schema(posicao) -> ChargePosition:
    return ChargePosition(
        base_amount=posicao.base,
        fine_amount=posicao.multa,
        interest_amount=posicao.juros,
        total_due=posicao.total_devido,
        paid_amount=posicao.pago,
        balance=posicao.saldo,
        days_overdue=posicao.dias_atraso,
        aging_bucket=faixa_aging(posicao.dias_atraso),
        reference_date=posicao.referencia,
        settled_at=posicao.data_quitacao,
    )


# ── Rotas estáticas antes de /{charge_id} (senão o Starlette devolve 405) ──


@router.get("/", response_model=List[ChargeListItem])
def list_charges(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, alias="status"),
    property_id: Optional[int] = Query(None),
    tenant_id: Optional[int] = Query(None),
    contract_id: Optional[int] = Query(None),
    competencia: Optional[date] = Query(None),
    due_from: Optional[date] = Query(None),
    due_to: Optional[date] = Query(None),
    only_open: bool = Query(False, description="Apenas cobranças com saldo em aberto"),
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    """Lista cobranças com a posição financeira de cada uma já calculada."""
    charges = repository.search(
        user_id=user_id,
        skip=skip,
        limit=limit,
        status=status_filter,
        property_id=property_id,
        tenant_id=tenant_id,
        contract_id=contract_id,
        competencia=competencia,
        due_from=due_from,
        due_to=due_to,
        only_open=only_open,
    )
    posicoes = repository.posicoes(charges)
    tenants, properties = repository.nomes_relacionados(charges, user_id)

    return [
        ChargeListItem(
            **ChargeRead.model_validate(charge).model_dump(),
            position=_posicao_schema(posicoes[charge.id]),
            tenant_name=tenants.get(charge.tenant_id),
            property_name=properties.get(charge.property_id),
        )
        for charge in charges
    ]


@router.post("/generate", response_model=GenerateChargesResponse)
def generate_charges(
    data: GenerateChargesRequest,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
):
    """
    Emite as cobranças da competência para os contratos ativos.

    Idempotente: reexecutar não duplica. O mesmo código roda no job diário.
    """
    if data.contract_id is not None:
        assert_owned(db, Contract, data.contract_id, user_id)

    resultado = gerar_cobrancas(
        db, user_id, competencia=data.competencia, contract_id=data.contract_id
    )
    return GenerateChargesResponse(**resultado)


@router.get("/aging", response_model=AgingReport)
def aging_report(
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    """
    Relatório de vencidos por faixa — o relatório padrão de inadimplência.

    Soma SALDO, não valor de face: quem pagou 600 de 1.000 entra por 400 mais
    encargos.
    """
    hoje = hoje_brt()
    baldes = repository.aging(user_id, hoje=hoje)

    buckets = [
        AgingBucket(
            bucket=nome,
            label=ROTULOS_AGING[nome],
            count=dados["count"],
            amount=dados["amount"],
        )
        for nome, dados in baldes.items()
    ]
    total_aberto = sum((b.amount for b in buckets), Decimal("0.00"))
    total_vencido = sum(
        (b.amount for b in buckets if b.bucket != "a_vencer"), Decimal("0.00")
    )
    return AgingReport(
        as_of=hoje,
        buckets=buckets,
        total_open=total_aberto,
        total_overdue=total_vencido,
    )


@router.get("/delinquency", response_model=List[dict])
def delinquency(
    limit: int = Query(50, ge=1, le=200),
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    """Uma linha por inquilino com dívida em aberto, do pior atraso ao menor."""
    return repository.resumo_inadimplencia(user_id, limite=limit)


@router.post("/", response_model=ChargeDetail, status_code=status.HTTP_201_CREATED)
def create_charge(
    data: ChargeCreate,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
    repository: ChargeRepository = Depends(get_repository),
):
    """Cria uma cobrança avulsa (fora da geração mensal)."""
    contract = assert_owned(db, Contract, data.contract_id, user_id)
    assert_owned_optional(db, Property, data.property_id, user_id)
    assert_owned_optional(db, Tenant, data.tenant_id, user_id)

    existente = (
        db.query(Charge)
        .filter(
            Charge.user_id == user_id,
            Charge.contract_id == data.contract_id,
            Charge.competencia == data.competencia.replace(day=1),
        )
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Já existe cobrança do contrato {data.contract_id} "
                f"para a competência {data.competencia:%m/%Y}"
            ),
        )

    charge = repository.create(data, user_id, contract)
    return _detalhe(repository, charge, user_id)


@router.get("/{charge_id}", response_model=ChargeDetail)
def get_charge(
    charge_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    charge = repository.get(charge_id, user_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada")
    return _detalhe(repository, charge, user_id)


@router.put("/{charge_id}", response_model=ChargeDetail)
def update_charge(
    charge_id: int,
    data: ChargeUpdate,
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    """
    Ajusta a composição da cobrança. `status` não é atualizável de propósito:
    ele é consequência do saldo, e digitá-lo permitiria marcar como quitada uma
    cobrança sem nenhum recebimento por trás.
    """
    charge = repository.get(charge_id, user_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada")
    if charge.status == CANCELADA:
        raise HTTPException(status_code=409, detail="Cobrança cancelada não pode ser alterada")

    charge = repository.update(charge, data)
    return _detalhe(repository, charge, user_id)


@router.post("/{charge_id}/cancel", response_model=ChargeDetail)
def cancel_charge(
    charge_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    """
    Cancela a cobrança preservando o histórico.

    Preferível a excluir: uma cobrança emitida por engano que some do banco
    leva junto os recebimentos aplicados a ela.
    """
    charge = repository.get(charge_id, user_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada")
    charge = repository.cancel(charge)
    return _detalhe(repository, charge, user_id)


@router.delete("/{charge_id}")
def delete_charge(
    charge_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    charge = repository.get(charge_id, user_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada")
    repository.delete(charge)
    return {"message": "Cobrança excluída com sucesso"}


# ── Recebimentos ─────────────────────────────────────────────────────────


@router.get("/{charge_id}/entries", response_model=List[PaymentEntryRead])
def list_entries(
    charge_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    charge = repository.get(charge_id, user_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada")
    return repository.entries_of(charge_id)


@router.post(
    "/{charge_id}/entries",
    response_model=ChargeDetail,
    status_code=status.HTTP_201_CREATED,
)
def add_entry(
    charge_id: int,
    data: PaymentEntryCreate,
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    """
    Registra um recebimento. Aceita valor parcial — esse é o ponto.

    Pagou 600 de uma cobrança de 1.000: a cobrança vira `parcial` e o saldo
    devedor (400 + multa + juros) passa a aparecer no painel, no extrato do
    inquilino e no aging. Um segundo recebimento de 400 depois quita a mesma
    cobrança, sem criar uma dívida fantasma.
    """
    charge = repository.get(charge_id, user_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada")
    if charge.status == CANCELADA:
        raise HTTPException(
            status_code=409, detail="Cobrança cancelada não aceita recebimento"
        )

    repository.add_entry(charge, data, user_id)
    return _detalhe(repository, charge, user_id)


@router.post("/{charge_id}/settle", response_model=ChargeDetail)
def settle_charge(
    charge_id: int,
    payment_date: Optional[date] = Query(None),
    method: Optional[str] = Query(None),
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    """
    Quita a cobrança registrando um recebimento do saldo exato de hoje.

    Atalho para o caso comum ("recebi tudo") sem que a tela precise calcular o
    valor com multa e juros do dia — cálculo que, feito no cliente, diverge do
    servidor no primeiro arredondamento.
    """
    charge = repository.get(charge_id, user_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada")
    if charge.status == CANCELADA:
        raise HTTPException(status_code=409, detail="Cobrança cancelada não aceita recebimento")

    data_pagamento = payment_date or hoje_brt()
    posicao = repository.posicoes([charge], hoje=data_pagamento)[charge.id]
    if posicao.saldo <= 0:
        raise HTTPException(status_code=409, detail="Cobrança já está quitada")

    repository.add_entry(
        charge,
        PaymentEntryCreate(
            date=data_pagamento,
            amount=posicao.saldo,
            method=method,
            description="Quitação total",
        ),
        user_id,
    )
    return _detalhe(repository, charge, user_id)


@router.delete("/{charge_id}/entries/{entry_id}")
def delete_entry(
    charge_id: int,
    entry_id: int,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
    repository: ChargeRepository = Depends(get_repository),
):
    """Estorna um recebimento lançado por engano; o status volta a refletir o saldo."""
    charge = repository.get(charge_id, user_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada")
    entry = (
        db.query(PaymentEntry)
        .filter(
            PaymentEntry.id == entry_id,
            PaymentEntry.charge_id == charge_id,
            PaymentEntry.user_id == user_id,
        )
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Recebimento não encontrado")

    repository.delete_entry(entry, charge)
    return {"message": "Recebimento estornado"}


def _detalhe(repository: ChargeRepository, charge: Charge, user_id: int) -> ChargeDetail:
    entries = repository.entries_of(charge.id)
    posicao = repository.posicoes([charge])[charge.id]
    tenants, properties = repository.nomes_relacionados([charge], user_id)
    return ChargeDetail(
        **ChargeRead.model_validate(charge).model_dump(),
        position=_posicao_schema(posicao),
        entries=[PaymentEntryRead.model_validate(e) for e in entries],
        tenant_name=tenants.get(charge.tenant_id),
        property_name=properties.get(charge.property_id),
    )
