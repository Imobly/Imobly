"""
Modelo SQLAlchemy da tabela `payments` — LEGADO, sem escrita.

A aplicação não grava mais aqui desde a revisão 0012: cobrança e recebimento
viraram `charges` + `payment_entries` (ver `src/charges/models.py`), porque uma
linha só não conseguia representar um aluguel de 1.000 pago em duas parcelas de
600 e 400.

A tabela continua no banco como rede de segurança da migração, e o modelo
continua mapeado para que o Alembic e os testes enxerguem o schema real. A
remoção de ambos fica para depois que os dados convertidos estiverem conferidos
em produção.
"""

from datetime import datetime
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from src.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    property_id = Column(
        Integer,
        ForeignKey("properties.id", name="fk_payment_property_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", name="fk_payment_tenant_id"),
        nullable=False,
        index=True,
    )
    contract_id = Column(
        Integer,
        ForeignKey("contracts.id", name="fk_payment_contract_id"),
        nullable=False,
        index=True,
    )
    due_date = Column(Date, nullable=False, index=True)
    payment_date = Column(Date, nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    # Multa e juros separados: somados num campo só, a composição da cobrança
    # ficava impossível de auditar.
    fine_amount = Column(Numeric(10, 2), nullable=False, server_default="0")
    interest_amount = Column(Numeric(10, 2), nullable=False, server_default="0")
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default="pendente", index=True)
    payment_method = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos serão definidos quando todos os módulos estiverem prontos
    # property = relationship("Property", back_populates="payments")
    # tenant = relationship("Tenant", back_populates="payments")
    # contract = relationship("Contract", back_populates="payments")
