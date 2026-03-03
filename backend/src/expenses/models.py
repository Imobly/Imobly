"""
Modelos SQLAlchemy para despesas
"""

from datetime import datetime
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON

from src.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    type = Column(String(20), nullable=False)
    property_id = Column(
        Integer,
        ForeignKey("properties.id", name="fk_expense_property_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    date = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    priority = Column(String(20), nullable=True)
    vendor = Column(String(255), nullable=True)
    number = Column(String(20), nullable=True)
    receipt = Column(Text, nullable=True)
    documents = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos serão definidos quando todos os módulos estiverem prontos
    # property = relationship("Property", back_populates="expenses")
