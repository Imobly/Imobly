"""
Modelo SQLAlchemy para o módulo de notificações
"""

from datetime import date, datetime
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, func

from src.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Tipo e conteúdo
    type = Column(
        String(50),
        nullable=False,
        default="system_alert",
    )  # contract_expiring | payment_overdue | maintenance_urgent | system_alert | reminder
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    date = Column(Date, nullable=False, default=date.today)

    # Flags
    priority = Column(String(20), nullable=False, default="medium")  # low | medium | high | urgent
    read_status = Column(Boolean, nullable=False, default=False)
    action_required = Column(Boolean, nullable=False, default=False)

    # Referência para entidade relacionada
    related_id = Column(String(50), nullable=True)
    related_type = Column(String(50), nullable=True)  # contract | payment | maintenance | property

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
