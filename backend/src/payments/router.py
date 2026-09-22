"""
Router de pagamentos — ADAPTADOR DE COMPATIBILIDADE sobre `charges`.

Estas rotas continuam existindo com o mesmo contrato para não quebrar o
frontend, mas não escrevem mais na tabela `payments`. Todas leem e gravam em
`charges` + `payment_entries`, que são a fonte da verdade desde a revisão 0012.

Manter as duas tabelas gravando dinheiro seria voltar ao problema que a
separação resolveu, só que com duas cópias divergentes em vez de uma errada.

Tradução de vocabulário (o cliente antigo não conhece os status novos):

    aberta   → pendente
    parcial  → parcial
    vencida  → atrasado
    quitada  → pago

Cobranças canceladas não aparecem por aqui: o status `cancelada` não existe no
vocabulário antigo, e devolvê-lo quebraria a validação do cliente.

Ganho imediato para quem usa a tela atual: `/register` com valor menor que o
devido agora GRAVA o saldo. Antes o restante era calculado e descartado.
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.charges.calculo import CANCELADA, QUITADA
from src.charges.models import Charge
from src.charges.repository import ChargeRepository
from src.charges.schema import ChargeCreate, ChargeUpdate, PaymentEntryCreate
from src.contracts.models import Contract
from src.core.ownership import assert_owned, assert_owned_optional
from src.core.tempo import hoje_brt
from src.database import get_db
from src.properties.models import Property
from src.security import get_current_user_local_id
from src.tenants.models import Tenant

from src.charges.encargos import calcular_pagamento
from .schema import (
    BulkConfirmRequest,
    PaymentCalculateRequest,
    PaymentCreate,
    PaymentRegisterRequest,
    PaymentResponse,
    PaymentUpdate,
)

router = APIRouter()

# charges → vocabulário antigo
_STATUS_LEGADO = {
    "aberta": "pendente",
    "parcial": "parcial",
    "vencida": "atrasado",
    "quitada": "pago",
}
# vocabulário antigo → charges (usado nos filtros de listagem)
_STATUS_NOVO = {v: k for k, v in _STATUS_LEGADO.items()}


def get_repository(db: Session = Depends(get_db)) -> ChargeRepository:
    return ChargeRepository(db)


def _legado(repository: ChargeRepository, charge: Charge, posicao=None) -> PaymentResponse:
    """Projeta uma cobrança no formato que o cliente antigo espera."""
    if posicao is None:
        posicao = repository.posicoes([charge])[charge.id]

    return PaymentResponse(
        id=charge.id,
        user_id=charge.user_id,
        property_id=charge.property_id,
        tenant_id=charge.tenant_id,
        contract_id=charge.contract_id,
        due_date=charge.due_date,
        payment_date=posicao.data_quitacao,
        amount=posicao.base,
        fine_amount=posicao.multa,
        interest_amount=posicao.juros,
        # `total_amount` passa a significar o TOTAL DEVIDO, que é o que o nome
        # sempre sugeriu. Em `/register` ele guardava o valor pago, e o painel
        # o lia como valor a receber — a mesma coluna respondendo duas
        # perguntas opostas. Quem quer o valor pago agora tem `paid_amount`.
        total_amount=posicao.total_devido,
        paid_amount=posicao.pago,
        balance_amount=posicao.saldo,
        days_overdue=posicao.dias_atraso,
        # Status vindo da POSIÇÃO calculada, não da coluna: se as duas
        # divergirem por um instante, é melhor o rótulo concordar com os
        # valores exibidos ao lado dele do que com o índice do banco.
        status=_STATUS_LEGADO.get(posicao.status, "pendente"),
        payment_method=None,
        description=charge.description,
        created_at=charge.created_at,
        updated_at=charge.updated_at,
    )


def _competencia_de(vencimento: date) -> date:
    return vencimento.replace(day=1)


def _charge_da_competencia(
    db: Session, user_id: int, contract_id: int, vencimento: date
) -> Optional[Charge]:
    return (
        db.query(Charge)
        .filter(
            Charge.user_id == user_id,
            Charge.contract_id == contract_id,
            Charge.competencia == _competencia_de(vencimento),
        )
        .first()
    )


@router.get("/", response_model=List[PaymentResponse])
def get_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="pendente | pago | atrasado | parcial"),
    property_id: Optional[int] = Query(None),
    tenant_id: Optional[int] = Query(None),
    contract_id: Optional[int] = Query(None),
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    """Lista cobranças no formato antigo. Filtros combináveis."""
    charges = repository.search(
        user_id=user_id,
        skip=skip,
        limit=limit,
        status=_STATUS_NOVO.get(status) if status else None,
        property_id=property_id,
        tenant_id=tenant_id,
        contract_id=contract_id,
    )
    charges = [c for c in charges if c.status != CANCELADA]
    posicoes = repository.posicoes(charges)
    return [_legado(repository, c, posicoes[c.id]) for c in charges]


# ── Rotas estáticas antes de /{payment_id} (senão o Starlette devolve 405) ──


@router.post("/calculate")
def calculate_payment(
    data: PaymentCalculateRequest,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
):
    """Simula multa e juros a partir das taxas do contrato, sem gravar nada."""
    contract = assert_owned(db, Contract, data.contract_id, user_id)

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
    repository: ChargeRepository = Depends(get_repository),
):
    """
    Registra um recebimento na cobrança da competência, criando-a se preciso.

    É aqui que o caso "aluguel de 1.000, pagou 600" passa a funcionar: o valor
    vira um recebimento, a cobrança fica `parcial` e o saldo de 400 mais multa e
    juros continua visível no painel, no extrato e no aging. Um segundo
    recebimento de 400 quita a MESMA cobrança, em vez de criar uma dívida
    fantasma.
    """
    contract = assert_owned(db, Contract, data.contract_id, user_id)
    assert_owned_optional(db, Property, data.property_id, user_id)
    assert_owned_optional(db, Tenant, data.tenant_id, user_id)

    charge = _charge_da_competencia(db, user_id, data.contract_id, data.due_date)
    if charge is None:
        charge = repository.create(
            ChargeCreate(
                contract_id=contract.id,
                property_id=data.property_id,
                tenant_id=data.tenant_id,
                competencia=_competencia_de(data.due_date),
                due_date=data.due_date,
                rent_amount=contract.rent,
                description=data.description,
            ),
            user_id,
            contract,
        )

    if charge.status == CANCELADA:
        raise HTTPException(status_code=409, detail="Cobrança cancelada não aceita recebimento")

    if data.paid_amount > 0:
        repository.add_entry(
            charge,
            PaymentEntryCreate(
                date=data.payment_date,
                amount=data.paid_amount,
                method=data.payment_method,
                description=data.description,
            ),
            user_id,
        )
    else:
        # Valor zero era o único jeito, no modelo antigo, de registrar uma
        # cobrança em aberto. Agora a cobrança já existe por si — não há
        # recebimento a lançar.
        repository.sincronizar_status(charge)

    db.refresh(charge)
    return _legado(repository, charge)


@router.get("/overdue/list", response_model=List[PaymentResponse])
def get_overdue_payments(
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    """
    Cobranças vencidas com saldo em aberto.

    A versão antiga filtrava por `status IN ('pendente','parcial')` com
    vencimento passado — mas o job diário das 06:00 já havia reescrito essas
    linhas para `atrasado`, então este endpoint devolvia lista vazia todo dia
    a partir das seis da manhã. Agora o critério é o saldo, não um rótulo que
    outro processo reescreve.
    """
    charges = repository.cobrancas_em_aberto(user_id)
    posicoes = repository.posicoes(charges)
    return [
        _legado(repository, c, posicoes[c.id])
        for c in charges
        if posicoes[c.id].dias_atraso > 0 and posicoes[c.id].saldo > 0
    ]


@router.post("/bulk-confirm/", response_model=List[PaymentResponse])
def bulk_confirm_payments(
    data: BulkConfirmRequest,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
    repository: ChargeRepository = Depends(get_repository),
):
    """
    Quita várias cobranças — tudo ou nada.

    Cada uma recebe um lançamento do próprio saldo na data informada, com multa
    e juros daquele dia. Confirmar em lote não é carimbar "pago": é registrar o
    dinheiro que entrou em cada cobrança.
    """
    data_pagamento = data.payment_date or hoje_brt()

    try:
        confirmadas: List[Charge] = []
        nao_encontrados: List[int] = []

        for charge_id in data.payment_ids:
            charge = repository.get(charge_id, user_id)
            if charge is None or charge.status == CANCELADA:
                nao_encontrados.append(charge_id)
                continue

            posicao = repository.posicoes([charge], hoje=data_pagamento)[charge.id]
            if posicao.saldo > 0:
                repository.add_entry(
                    charge,
                    PaymentEntryCreate(
                        date=data_pagamento,
                        amount=posicao.saldo,
                        description="Confirmação em lote",
                    ),
                    user_id,
                    commit=False,
                )
            confirmadas.append(charge)

        if nao_encontrados:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cobranças não encontradas: {nao_encontrados}",
            )

        db.commit()
    except Exception:
        db.rollback()
        raise

    for charge in confirmadas:
        db.refresh(charge)
    return [_legado(repository, c) for c in confirmadas]


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment_data: PaymentCreate,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
    repository: ChargeRepository = Depends(get_repository),
):
    """
    Cria a cobrança da competência no formato antigo.

    `status` do payload não é gravado: se vier `pago` ou `parcial` com data de
    pagamento, o valor correspondente é lançado como RECEBIMENTO. Gravar o
    rótulo direto era o que permitia existir cobrança "paga" sem um centavo
    registrado atrás dela.
    """
    assert_owned(db, Property, payment_data.property_id, user_id)
    assert_owned(db, Tenant, payment_data.tenant_id, user_id)
    contract = assert_owned(db, Contract, payment_data.contract_id, user_id)

    if _charge_da_competencia(db, user_id, payment_data.contract_id, payment_data.due_date):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Já existe cobrança do contrato {payment_data.contract_id} "
                f"para a competência {payment_data.due_date:%m/%Y}"
            ),
        )

    charge = repository.create(
        ChargeCreate(
            contract_id=payment_data.contract_id,
            property_id=payment_data.property_id,
            tenant_id=payment_data.tenant_id,
            competencia=_competencia_de(payment_data.due_date),
            due_date=payment_data.due_date,
            rent_amount=payment_data.amount,
            description=payment_data.description,
        ),
        user_id,
        contract,
    )

    if payment_data.status in ("pago", "parcial") and payment_data.payment_date:
        posicao = repository.posicoes([charge], hoje=payment_data.payment_date)[charge.id]
        valor = (
            posicao.total_devido
            if payment_data.status == "pago"
            else payment_data.total_amount
        )
        if valor > 0:
            repository.add_entry(
                charge,
                PaymentEntryCreate(
                    date=payment_data.payment_date,
                    amount=valor,
                    method=payment_data.payment_method,
                    description=payment_data.description,
                ),
                user_id,
            )

    db.refresh(charge)
    return _legado(repository, charge)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    charge = repository.get(payment_id, user_id)
    if not charge or charge.status == CANCELADA:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return _legado(repository, charge)


@router.put("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    """
    Atualiza a cobrança. `status: "pago"` vira uma QUITAÇÃO — um recebimento do
    saldo na data informada —, não um rótulo gravado à mão.
    """
    charge = repository.get(payment_id, user_id)
    if not charge or charge.status == CANCELADA:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    campos = payment_data.model_dump(exclude_unset=True)
    alteracoes = ChargeUpdate(
        rent_amount=campos.get("amount"),
        description=campos.get("description"),
    )
    if alteracoes.model_dump(exclude_none=True):
        charge = repository.update(charge, alteracoes)

    if campos.get("status") == "pago" and charge.status != QUITADA:
        data_pagamento = campos.get("payment_date") or hoje_brt()
        posicao = repository.posicoes([charge], hoje=data_pagamento)[charge.id]
        if posicao.saldo > 0:
            repository.add_entry(
                charge,
                PaymentEntryCreate(
                    date=data_pagamento,
                    amount=posicao.saldo,
                    method=campos.get("payment_method"),
                    description=campos.get("description"),
                ),
                user_id,
            )

    return _legado(repository, charge)


@router.delete("/{payment_id}")
def delete_payment(
    payment_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    charge = repository.get(payment_id, user_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    repository.delete(charge)
    return {"message": "Pagamento deletado com sucesso"}


@router.post("/{payment_id}/confirm/", response_model=PaymentResponse)
def confirm_payment(
    payment_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repository: ChargeRepository = Depends(get_repository),
):
    """Quita a cobrança lançando um recebimento do saldo de hoje."""
    charge = repository.get(payment_id, user_id)
    if not charge or charge.status == CANCELADA:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    hoje = hoje_brt()
    posicao = repository.posicoes([charge], hoje=hoje)[charge.id]
    if posicao.saldo > 0:
        repository.add_entry(
            charge,
            PaymentEntryCreate(date=hoje, amount=posicao.saldo, description="Confirmação"),
            user_id,
        )
    return _legado(repository, charge)
