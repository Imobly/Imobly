from datetime import datetime

from sqlalchemy import JSON, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # Reference to user in auth-api
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    cpf_cnpj = Column(String(20), unique=True, nullable=False)
    birth_date = Column(Date, nullable=True)
    profession = Column(String(100), nullable=False)
    emergency_contact = Column(JSON)  # {name, phone, relationship}
    documents = Column(JSON)  # Array de documentos {id, name, type, url}
    contract_id = Column(
        Integer,
        ForeignKey("contracts.id", name="fk_tenant_contract_id", use_alter=True),
        nullable=True,
    )  # Contrato ativo
    status = Column(String(20), default="active")  # 'active', 'inactive'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    contract = relationship("Contract", foreign_keys=[contract_id], uselist=False)  # Contrato ativo
    contracts = relationship("Contract", foreign_keys="Contract.tenant_id", back_populates="tenant")
    payments = relationship("Payment", back_populates="tenant")
