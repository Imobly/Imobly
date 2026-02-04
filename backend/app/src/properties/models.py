from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # Reference to user in auth-api
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    neighborhood = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    zip_code = Column(String(20), nullable=False)
    type = Column(String(50), nullable=False)  # 'apartment', 'house', 'commercial', 'studio'
    area = Column(Numeric(10, 2), nullable=False)
    bedrooms = Column(Integer, nullable=False)
    bathrooms = Column(Integer, nullable=False)
    parking_spaces = Column(Integer, default=0)
    rent = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default="vacant")  # 'vacant', 'occupied', 'maintenance', 'inactive'
    description = Column(Text)
    images = Column(JSON)  # Array de URLs das imagens
    is_residential = Column(Boolean, default=True)
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", name="fk_property_tenant_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    units = relationship("Unit", back_populates="property", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="property")
    payments = relationship("Payment", back_populates="property")
    expenses = relationship("Expense", back_populates="property")
    # maintenances = relationship("Maintenance", back_populates="property")
