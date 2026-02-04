from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # Reference to user in auth-api
    title = Column(String(255), nullable=False)
    property_id = Column(
        Integer, ForeignKey("properties.id", name="fk_contract_property_id"), nullable=False
    )
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", name="fk_contract_tenant_id"), nullable=False
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    rent = Column(Numeric(10, 2), nullable=False)
    deposit = Column(Numeric(10, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)  # Taxa de juros mensal
    fine_rate = Column(Numeric(5, 2), nullable=False)  # Taxa de multa
    status = Column(String(20), default="active")  # 'active', 'expired', 'terminated'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    property = relationship("Property", back_populates="contracts")
    tenant = relationship("Tenant", foreign_keys=[tenant_id], back_populates="contracts")
    payments = relationship("Payment", back_populates="contract")
