import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, nullable=False, index=True)  # Reference to user in auth-api
    type = Column(
        String(50), nullable=False
    )  # 'contract_expiring', 'payment_overdue', 'maintenance_urgent', 'system_alert', 'reminder'
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False)
    priority = Column(String(20), nullable=False)  # 'low', 'medium', 'high', 'urgent'
    read_status = Column(Boolean, default=False)
    action_required = Column(Boolean, default=False)
    related_id = Column(String(255), nullable=True)
    related_type = Column(
        String(50), nullable=True
    )  # 'contract', 'payment', 'maintenance', 'property'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
