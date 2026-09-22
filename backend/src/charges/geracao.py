"""
Geração das cobranças mensais a partir dos contratos ativos.

Isto não existia. O `due_day` do contrato estava no modelo e nenhuma linha do
sistema o lia: a parcela de cada mês teria que ser digitada à mão, contrato a
contrato. Com três imóveis dá; com oitenta, a inadimplência que o painel mostra
é só o reflexo do que alguém lembrou de lançar.

A operação é idempotente por (contrato, competência) — garantida também no
banco pela UNIQUE `ux_charges_contrato_competencia`. Rodar o job duas vezes no
mesmo mês, ou clicar no botão manual depois do job automático, não gera
cobrança duplicada para o inquilino.
"""

from __future__ import annotations

import calendar
import logging
from datetime import date
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.contracts.models import Contract
from src.core.tempo import hoje_brt

from .models import Charge

logger = logging.getLogger("imobly.charges.geracao")


def primeiro_dia(referencia: date) -> date:
    return referencia.replace(day=1)


def vencimento_na_competencia(competencia: date, due_day: int) -> date:
    """
    Resolve o dia de vencimento dentro do mês da competência.

    Contrato com vencimento no dia 31 em mês de 30 dias cai no último dia, e
    não estoura. Fevereiro é o caso que quebra na prática todo ano.
    """
    ultimo = calendar.monthrange(competencia.year, competencia.month)[1]
    return competencia.replace(day=min(max(due_day, 1), ultimo))


def gerar_cobrancas(
    db: Session,
    user_id: int,
    competencia: Optional[date] = None,
    contract_id: Optional[int] = None,
    commit: bool = True,
) -> Dict[str, object]:
    """
    Emite as cobranças da competência para os contratos ativos do usuário.

    Só entram contratos vigentes NA competência: um contrato que terminou em
    agosto não gera cobrança de setembro, mesmo que ainda esteja marcado como
    ativo por o job de expiração não ter rodado.
    """
    competencia = primeiro_dia(competencia or hoje_brt())

    q = db.query(Contract).filter(
        Contract.user_id == user_id,
        Contract.status == "ativo",
        Contract.start_date <= competencia,
    )
    if contract_id is not None:
        q = q.filter(Contract.id == contract_id)
    contratos = q.all()

    # Contratos que já têm cobrança nesta competência — uma query, não uma por
    # contrato.
    ja_emitidos = {
        cid
        for (cid,) in db.query(Charge.contract_id)
        .filter(Charge.user_id == user_id, Charge.competencia == competencia)
        .all()
    }

    criadas: List[Charge] = []
    pulados_existentes = 0
    pulados_sem_dia = 0

    for contrato in contratos:
        # Vigência: o fim do contrato tem que alcançar a competência.
        if contrato.end_date and contrato.end_date < competencia:
            continue
        if contrato.id in ja_emitidos:
            pulados_existentes += 1
            continue
        if not contrato.due_day:
            # Sem dia de vencimento não há como calcular atraso, e uma cobrança
            # com vencimento arbitrado geraria multa que ninguém combinou.
            pulados_sem_dia += 1
            logger.warning(
                "Contrato %s sem due_day — cobrança de %s não emitida",
                contrato.id,
                competencia,
            )
            continue

        charge = Charge(
            user_id=user_id,
            contract_id=contrato.id,
            property_id=contrato.property_id,
            tenant_id=contrato.tenant_id,
            competencia=competencia,
            due_date=vencimento_na_competencia(competencia, contrato.due_day),
            rent_amount=contrato.rent,
            charges_amount=0,
            discount_amount=0,
            # Taxas congeladas na emissão: um reajuste posterior não pode
            # alterar retroativamente o que já foi cobrado.
            fine_rate=contrato.fine_rate or 0,
            interest_rate=contrato.interest_rate or 0,
            status="aberta",
            description=f"Aluguel {competencia:%m/%Y}",
        )
        db.add(charge)
        criadas.append(charge)

    if criadas:
        db.flush()
    if commit:
        db.commit()

    return {
        "competencia": competencia,
        "created": len(criadas),
        "skipped_existing": pulados_existentes,
        "skipped_no_due_day": pulados_sem_dia,
        "charge_ids": [c.id for c in criadas],
    }
