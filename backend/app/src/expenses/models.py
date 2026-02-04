import uuid
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, nullable=False, index=True)  # Reference to user in auth-api
    type = Column(String(20), nullable=False, default="expense")  # 'expense', 'maintenance'
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    date = Column(Date, nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    status = Column(String(20), nullable=False)  # 'pending', 'paid', 'scheduled'
    priority = Column(String(20), nullable=True)  # 'low', 'medium', 'high', 'urgent'
    vendor = Column(String(255), nullable=True)
    number = Column(String(20), nullable=True)  # Telefone/contato do fornecedor
    receipt = Column(Text, nullable=True)  # URL do comprovante (DEPRECATED - usar documents)
    documents = Column(JSONB, nullable=True, default=[])  # Array de documentos/comprovantes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    property = relationship("Property", back_populates="expenses")
