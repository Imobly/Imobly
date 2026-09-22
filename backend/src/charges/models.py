"""
Modelos SQLAlchemy para cobranças (charges) e recebimentos (payment_entries).

Por que duas tabelas em vez da `payments` antiga:

`payments` tratava um pagamento como UM EVENTO. Mas a realidade da locação é
uma COBRANÇA (competência 09/2026, vence dia 10, R$ 1.000) que pode receber N
RECEBIMENTOS (R$ 600 no dia 10, R$ 400 no dia 20). Com uma linha só, um
pagamento parcial não tinha onde ser representado: ou se criava uma segunda
linha — que o dashboard somava como se fosse outra dívida — ou se sobrescrevia
a primeira, perdendo a trilha de auditoria.

O saldo devedor NÃO é uma coluna. Ele é `total_devido(hoje) - soma(recebimentos)`,
calculado em `calculo.py`, porque multa e juros de uma dívida em aberto crescem
todo dia: congelá-los numa coluna faria o painel mostrar um número que parou no
tempo.
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from src.database import Base


class Charge(Base):
    """Uma cobrança mensal de um contrato."""

    __tablename__ = "charges"

    __table_args__ = (
        # Idempotência da geração mensal: rodar o job duas vezes no mesmo mês
        # não pode duplicar a cobrança do inquilino.
        UniqueConstraint("contract_id", "competencia", name="ux_charges_contrato_competencia"),
        Index("ix_charges_user_status_due", "user_id", "status", "due_date"),
        Index("ix_charges_user_tenant", "user_id", "tenant_id"),
        CheckConstraint(
            "status IN ('aberta','parcial','vencida','quitada','cancelada')",
            name="ck_charges_status",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    contract_id = Column(
        Integer,
        ForeignKey("contracts.id", name="fk_charge_contract_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Desnormalizados a partir do contrato: as telas filtram por imóvel e por
    # inquilino o tempo todo, e o contrato pode ser trocado sem que a cobrança
    # já emitida mude de dono.
    property_id = Column(
        Integer,
        ForeignKey("properties.id", name="fk_charge_property_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", name="fk_charge_tenant_id"),
        nullable=False,
        index=True,
    )

    # Primeiro dia do mês de competência — a que mês o aluguel se refere.
    # Distinto de `due_date`: o aluguel de setembro pode vencer em 05/10.
    competencia = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)

    # Composição do valor. `charges_amount` agrega encargos (condomínio, IPTU,
    # água) num campo só por ora; quando cada encargo precisar de destino
    # próprio, vira tabela filha sem alterar o resto do cálculo.
    rent_amount = Column(Numeric(10, 2), nullable=False)
    charges_amount = Column(Numeric(10, 2), nullable=False, server_default="0")
    discount_amount = Column(Numeric(10, 2), nullable=False, server_default="0")

    # Taxas CONGELADAS na emissão, não lidas do contrato na hora do cálculo.
    # Um reajuste de multa/juros não pode alterar retroativamente o que já foi
    # cobrado — a cobrança de março tem que continuar reproduzindo o número que
    # o inquilino recebeu em março.
    fine_rate = Column(Numeric(5, 2), nullable=False, server_default="0")
    interest_rate = Column(Numeric(5, 2), nullable=False, server_default="0")

    # Derivado do saldo, nunca informado pelo cliente. Existe como coluna para
    # que filtro e agregação aconteçam no banco; a verdade continua sendo o
    # cálculo em `calculo.py`, e `repository.sincronizar_status` reconcilia os
    # dois. Ver a nota em `schema.ChargeCreate`.
    status = Column(String(20), nullable=False, server_default="aberta", index=True)

    description = Column(Text, nullable=True)
    canceled_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PaymentEntry(Base):
    """Um recebimento aplicado a uma cobrança. Várias por cobrança."""

    __tablename__ = "payment_entries"

    __table_args__ = (
        Index("ix_payment_entries_charge_date", "charge_id", "date"),
        CheckConstraint("amount > 0", name="ck_payment_entries_amount_positivo"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    charge_id = Column(
        Integer,
        ForeignKey("charges.id", name="fk_entry_charge_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    method = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
