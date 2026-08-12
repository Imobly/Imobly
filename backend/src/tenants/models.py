"""
Modelos SQLAlchemy para inquilinos (tenants)
"""

from datetime import datetime
from sqlalchemy import JSON, Column, Date, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import relationship

from src.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    # Unicidade é POR LOCADOR, não global: dois locadores podem ter o mesmo
    # inquilino (cenário corriqueiro). Antes eram UNIQUE globais, o que gerava
    # 500 no cadastro e permitia enumerar inquilinos de outros clientes.
    __table_args__ = (
        Index("ux_tenants_user_email", "user_id", text("lower(email)"), unique=True),
        Index("ux_tenants_user_cpf", "user_id", "cpf_cnpj", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # dono (locador)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    cpf_cnpj = Column(String(20), nullable=False)
    birth_date = Column(Date, nullable=True)
    profession = Column(String(100), nullable=False)
    emergency_contact = Column(JSON)  # {name, phone, relationship}
    documents = Column(JSON)  # Array de documentos {id, name, type, url}
    contract_id = Column(
        Integer,
        ForeignKey("contracts.id", name="fk_tenant_contract_id", use_alter=True),
        nullable=True,
    )  # Contrato ativo
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos serão definidos quando todos os módulos estiverem prontos
    # contract = relationship("Contract", foreign_keys=[contract_id], uselist=False)
    # contracts = relationship("Contract", foreign_keys="Contract.tenant_id", back_populates="tenant")
    # payments = relationship("Payment", back_populates="tenant")