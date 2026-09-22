"""
Repository de cobranças e recebimentos.

Regra de carregamento: a posição de uma cobrança depende dos recebimentos
dela. Listar N cobranças e buscar os recebimentos de cada uma seria N+1 — com
uma carteira de 200 imóveis, 200 queries por tela. Todos os métodos de
listagem carregam os recebimentos do conjunto inteiro numa query só e
distribuem em memória.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from src.contracts.models import Contract
from src.core.tempo import hoje_brt
from src.properties.models import Property
from src.tenants.models import Tenant

from .calculo import (
    CANCELADA,
    FAIXAS_AGING,
    QUITADA,
    STATUS_EM_ABERTO,
    PosicaoCobranca,
    Recebimento,
    faixa_aging,
    posicao_de,
    situacao_inquilino,
)
from .models import Charge, PaymentEntry
from .schema import ChargeCreate, ChargeUpdate, PaymentEntryCreate


class ChargeRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Leitura ──────────────────────────────────────────────────────────

    def get(self, charge_id: int, user_id: int) -> Optional[Charge]:
        return (
            self.db.query(Charge)
            .filter(Charge.id == charge_id, Charge.user_id == user_id)
            .first()
        )

    def entries_of(self, charge_id: int) -> List[PaymentEntry]:
        return (
            self.db.query(PaymentEntry)
            .filter(PaymentEntry.charge_id == charge_id)
            .order_by(PaymentEntry.date, PaymentEntry.id)
            .all()
        )

    def _entries_by_charge(self, charge_ids: Sequence[int]) -> Dict[int, List[Recebimento]]:
        """Recebimentos de várias cobranças numa query só (anti N+1)."""
        agrupados: Dict[int, List[Recebimento]] = defaultdict(list)
        if not charge_ids:
            return agrupados
        linhas = (
            self.db.query(PaymentEntry.charge_id, PaymentEntry.date, PaymentEntry.amount)
            .filter(PaymentEntry.charge_id.in_(list(charge_ids)))
            .order_by(PaymentEntry.date, PaymentEntry.id)
            .all()
        )
        for charge_id, data, valor in linhas:
            agrupados[charge_id].append(Recebimento(data=data, valor=Decimal(str(valor))))
        return agrupados

    def search(
        self,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        property_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        contract_id: Optional[int] = None,
        competencia: Optional[date] = None,
        due_from: Optional[date] = None,
        due_to: Optional[date] = None,
        only_open: bool = False,
    ) -> List[Charge]:
        """
        Filtros COMBINÁVEIS — todos aplicados em sequência, nunca em if/elif.

        `status` aqui usa a coluna derivada, que é reconciliada a cada
        recebimento e pelo job diário. Ela serve para filtrar no banco; o valor
        exibido vem sempre da posição recalculada.
        """
        q = self.db.query(Charge).filter(Charge.user_id == user_id)

        if status:
            q = q.filter(Charge.status == status)
        if only_open:
            q = q.filter(Charge.status.in_(STATUS_EM_ABERTO))
        if property_id is not None:
            q = q.filter(Charge.property_id == property_id)
        if tenant_id is not None:
            q = q.filter(Charge.tenant_id == tenant_id)
        if contract_id is not None:
            q = q.filter(Charge.contract_id == contract_id)
        if competencia is not None:
            q = q.filter(Charge.competencia == competencia)
        if due_from is not None:
            q = q.filter(Charge.due_date >= due_from)
        if due_to is not None:
            q = q.filter(Charge.due_date <= due_to)

        return (
            q.order_by(Charge.due_date.desc(), Charge.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def posicoes(
        self, charges: Sequence[Charge], hoje: Optional[date] = None
    ) -> Dict[int, PosicaoCobranca]:
        """Posição de um conjunto de cobranças, com uma única query de recebimentos."""
        hoje = hoje or hoje_brt()
        recebimentos = self._entries_by_charge([c.id for c in charges])
        return {c.id: posicao_de(c, recebimentos.get(c.id, []), hoje=hoje) for c in charges}

    def nomes_relacionados(
        self, charges: Sequence[Charge], user_id: int
    ) -> Tuple[Dict[int, str], Dict[int, str]]:
        """
        Nome do inquilino e do imóvel em duas queries, filtrando por dono.

        O predicado de posse vai na query dos nomes também: uma cobrança com FK
        apontando para entidade de terceiro não pode revelar o nome dela.
        """
        tenant_ids = {c.tenant_id for c in charges}
        property_ids = {c.property_id for c in charges}

        tenants: Dict[int, str] = {}
        if tenant_ids:
            tenants = dict(
                self.db.query(Tenant.id, Tenant.name)
                .filter(Tenant.id.in_(tenant_ids), Tenant.user_id == user_id)
                .all()
            )
        properties: Dict[int, str] = {}
        if property_ids:
            properties = dict(
                self.db.query(Property.id, Property.name)
                .filter(Property.id.in_(property_ids), Property.user_id == user_id)
                .all()
            )
        return tenants, properties

    # ── Escrita ──────────────────────────────────────────────────────────

    def create(self, data: ChargeCreate, user_id: int, contract: Contract) -> Charge:
        """Cria a cobrança copiando taxas e vínculos do contrato."""
        charge = Charge(
            user_id=user_id,
            contract_id=contract.id,
            property_id=data.property_id or contract.property_id,
            tenant_id=data.tenant_id or contract.tenant_id,
            competencia=data.competencia.replace(day=1),
            due_date=data.due_date,
            rent_amount=data.rent_amount,
            charges_amount=data.charges_amount,
            discount_amount=data.discount_amount,
            fine_rate=contract.fine_rate or 0,
            interest_rate=contract.interest_rate or 0,
            description=data.description,
            status="aberta",
        )
        self.db.add(charge)
        self.db.flush()
        self.sincronizar_status(charge, commit=False)
        self.db.commit()
        self.db.refresh(charge)
        return charge

    def update(self, charge: Charge, data: ChargeUpdate) -> Charge:
        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(charge, campo, valor)
        self.sincronizar_status(charge, commit=False)
        self.db.commit()
        self.db.refresh(charge)
        return charge

    def add_entry(
        self, charge: Charge, data: PaymentEntryCreate, user_id: int, commit: bool = True
    ) -> PaymentEntry:
        """
        Registra um recebimento e reconcilia o status da cobrança.

        Nada de somar no total existente: o recebimento é uma linha nova. É
        isso que permite ao inquilino pagar 600 hoje e 400 daqui a dez dias sem
        que a cobrança original seja adulterada.
        """
        entry = PaymentEntry(
            user_id=user_id,
            charge_id=charge.id,
            date=data.date,
            amount=data.amount,
            method=data.method,
            description=data.description,
        )
        self.db.add(entry)
        self.db.flush()
        self.sincronizar_status(charge, commit=False)
        if commit:
            self.db.commit()
            self.db.refresh(entry)
            self.db.refresh(charge)
        return entry

    def delete_entry(self, entry: PaymentEntry, charge: Charge) -> None:
        self.db.delete(entry)
        self.db.flush()
        self.sincronizar_status(charge, commit=False)
        self.db.commit()

    def cancel(self, charge: Charge) -> Charge:
        charge.status = CANCELADA
        charge.canceled_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(charge)
        return charge

    def delete(self, charge: Charge) -> None:
        self.db.delete(charge)
        self.db.commit()

    def sincronizar_status(
        self, charge: Charge, hoje: Optional[date] = None, commit: bool = True
    ) -> str:
        """
        Reconcilia a coluna `status` com a posição calculada.

        Cobrança cancelada não é recalculada — cancelamento é decisão
        administrativa e não pode ser desfeito por um job.
        """
        if charge.status == CANCELADA:
            return CANCELADA

        recebimentos = [
            Recebimento(data=e.date, valor=Decimal(str(e.amount)))
            for e in self.entries_of(charge.id)
        ]
        posicao = posicao_de(charge, recebimentos, hoje=hoje)
        if charge.status != posicao.status:
            charge.status = posicao.status
        if commit:
            self.db.commit()
        return posicao.status

    def sincronizar_status_em_lote(self, user_id: int, hoje: Optional[date] = None) -> int:
        """
        Reconcilia o status de todas as cobranças em aberto de um usuário.

        Usado pelo job diário: o que muda sozinho com o passar do tempo é
        `aberta` → `vencida`. O UPDATE em massa antigo marcava `parcial` como
        `atrasado`, apagando a informação de que houve pagamento; aqui a
        transição sai do cálculo, então `parcial` continua `parcial`.
        """
        hoje = hoje or hoje_brt()
        charges = (
            self.db.query(Charge)
            .filter(Charge.user_id == user_id, Charge.status.in_(STATUS_EM_ABERTO))
            .all()
        )
        recebimentos = self._entries_by_charge([c.id for c in charges])
        alteradas = 0
        for charge in charges:
            posicao = posicao_de(charge, recebimentos.get(charge.id, []), hoje=hoje)
            if charge.status != posicao.status:
                charge.status = posicao.status
                alteradas += 1
        if alteradas:
            self.db.commit()
        return alteradas

    # ── Agregações de gestão ─────────────────────────────────────────────

    def cobrancas_em_aberto(self, user_id: int, tenant_id: Optional[int] = None) -> List[Charge]:
        q = self.db.query(Charge).filter(
            Charge.user_id == user_id, Charge.status.in_(STATUS_EM_ABERTO)
        )
        if tenant_id is not None:
            q = q.filter(Charge.tenant_id == tenant_id)
        return q.order_by(Charge.due_date).all()

    def aging(self, user_id: int, hoje: Optional[date] = None) -> Dict[str, Dict[str, object]]:
        """
        Vencidos por faixa (1-30 / 31-60 / 61-90 / 90+), somando SALDO — não
        valor de face. Uma cobrança de R$ 1.000 com R$ 600 recebidos entra no
        relatório por R$ 400 mais encargos, que é o que se cobra de fato.
        """
        hoje = hoje or hoje_brt()
        charges = self.cobrancas_em_aberto(user_id)
        recebimentos = self._entries_by_charge([c.id for c in charges])

        baldes: Dict[str, Dict[str, object]] = {
            nome: {"count": 0, "amount": Decimal("0.00")} for nome, _, _ in FAIXAS_AGING
        }
        for charge in charges:
            posicao = posicao_de(charge, recebimentos.get(charge.id, []), hoje=hoje)
            if posicao.saldo <= 0:
                continue
            balde = baldes[faixa_aging(posicao.dias_atraso)]
            balde["count"] += 1
            balde["amount"] += posicao.saldo
        return baldes

    def ledger_do_inquilino(
        self, user_id: int, tenant_id: int, hoje: Optional[date] = None
    ) -> Dict[str, object]:
        """
        Posição financeira completa de um inquilino: saldo em aberto, atraso
        mais antigo, situação e histórico de pontualidade.
        """
        hoje = hoje or hoje_brt()
        todas = (
            self.db.query(Charge)
            .filter(
                Charge.user_id == user_id,
                Charge.tenant_id == tenant_id,
                Charge.status != CANCELADA,
            )
            .order_by(Charge.due_date.desc())
            .all()
        )
        recebimentos = self._entries_by_charge([c.id for c in todas])

        saldo_aberto = Decimal("0.00")
        saldo_vencido = Decimal("0.00")
        atraso_mais_antigo = 0
        abertas = 0
        quitadas = 0
        quitadas_em_dia = 0
        soma_atraso = 0

        itens: List[Tuple[Charge, PosicaoCobranca]] = []
        for charge in todas:
            posicao = posicao_de(charge, recebimentos.get(charge.id, []), hoje=hoje)
            itens.append((charge, posicao))

            if posicao.status == QUITADA:
                quitadas += 1
                if posicao.dias_atraso <= 0:
                    quitadas_em_dia += 1
                soma_atraso += posicao.dias_atraso
            else:
                abertas += 1
                saldo_aberto += posicao.saldo
                if posicao.dias_atraso > 0:
                    saldo_vencido += posicao.saldo
                    atraso_mais_antigo = max(atraso_mais_antigo, posicao.dias_atraso)

        return {
            "as_of": hoje,
            "situacao": situacao_inquilino(atraso_mais_antigo, saldo_aberto),
            "open_balance": saldo_aberto,
            "overdue_balance": saldo_vencido,
            "oldest_overdue_days": atraso_mais_antigo,
            "open_charges": abertas,
            "charges_settled": quitadas,
            "settled_on_time": quitadas_em_dia,
            "on_time_rate": (quitadas_em_dia / quitadas * 100) if quitadas else 0.0,
            "average_delay_days": (soma_atraso / quitadas) if quitadas else 0.0,
            "itens": itens,
        }

    def resumo_inadimplencia(
        self, user_id: int, hoje: Optional[date] = None, limite: int = 50
    ) -> List[Dict[str, object]]:
        """
        Uma linha por inquilino com dívida em aberto, ordenada pelo atraso.

        É o que o dashboard precisa mostrar: o painel antigo listava
        `Payment.total_amount` como "valor devido", e nos registros parciais
        esse campo guardava o valor PAGO — o número exibido era o oposto do
        pretendido.
        """
        hoje = hoje or hoje_brt()
        charges = self.cobrancas_em_aberto(user_id)
        if not charges:
            return []

        recebimentos = self._entries_by_charge([c.id for c in charges])
        tenants, properties = self.nomes_relacionados(charges, user_id)

        por_inquilino: Dict[int, Dict[str, object]] = {}
        for charge in charges:
            posicao = posicao_de(charge, recebimentos.get(charge.id, []), hoje=hoje)
            if posicao.saldo <= 0:
                continue
            item = por_inquilino.setdefault(
                charge.tenant_id,
                {
                    "tenant_id": charge.tenant_id,
                    "tenant_name": tenants.get(charge.tenant_id, "—"),
                    "property_id": charge.property_id,
                    "property_name": properties.get(charge.property_id, "—"),
                    "balance": Decimal("0.00"),
                    "overdue_balance": Decimal("0.00"),
                    "open_charges": 0,
                    "oldest_due_date": charge.due_date,
                    "days_overdue": 0,
                },
            )
            item["balance"] += posicao.saldo
            item["open_charges"] += 1
            if posicao.dias_atraso > 0:
                item["overdue_balance"] += posicao.saldo
                if posicao.dias_atraso > item["days_overdue"]:
                    item["days_overdue"] = posicao.dias_atraso
                    item["oldest_due_date"] = charge.due_date

        linhas = list(por_inquilino.values())
        for linha in linhas:
            linha["situacao"] = situacao_inquilino(linha["days_overdue"], linha["balance"])
        linhas.sort(key=lambda l: (-l["days_overdue"], -l["balance"]))
        return linhas[:limite]
