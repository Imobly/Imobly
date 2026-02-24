"""
Modelos SQLAlchemy para contratos
"""

from datetime import datetime
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from src.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # owner (landlord)
    title = Column(String(255), nullable=False)
    property_id = Column(
        Integer,
        ForeignKey("properties.id", name="fk_contract_property_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", name="fk_contract_tenant_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    rent = Column(Numeric(10, 2), nullable=False)
    deposit = Column(Numeric(10, 2), default=0)
    interest_rate = Column(Numeric(5, 2), default=0)   # % per month on late payment
    fine_rate = Column(Numeric(5, 2), default=0)        # % fine on late payment
    status = Column(String(20), default="active")       # 'active', 'expired', 'terminated'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
