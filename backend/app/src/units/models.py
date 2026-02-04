from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # Reference to user in auth-api
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    number = Column(String(50), nullable=False)
    area = Column(Numeric(10, 2), nullable=False)
    bedrooms = Column(Integer, nullable=False)
    bathrooms = Column(Integer, nullable=False)
    rent = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False)  # 'vacant', 'occupied', 'maintenance'
    tenant = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    property = relationship("Property", back_populates="units")
