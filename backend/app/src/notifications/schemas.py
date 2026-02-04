from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NotificationBase(BaseModel):
    type: str = Field(
        ...,
        pattern="^(contract_expiring|payment_overdue|maintenance_urgent|system_alert|reminder)$",
    )
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    date: datetime
    priority: str = Field(..., pattern="^(low|medium|high|urgent)$")
    read_status: bool = False
    action_required: bool = False
    related_id: Optional[str] = None
    related_type: Optional[str] = Field(None, pattern="^(contract|payment|maintenance|property)$")


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    type: Optional[str] = Field(
        None,
        pattern="^(contract_expiring|payment_overdue|maintenance_urgent|system_alert|reminder)$",
    )
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    message: Optional[str] = None
    date: Optional[datetime] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    read_status: Optional[bool] = None
    action_required: Optional[bool] = None
    related_id: Optional[str] = None
    related_type: Optional[str] = Field(None, pattern="^(contract|payment|maintenance|property)$")


class NotificationResponse(NotificationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Alias para Response
Notification = NotificationResponse


class NotificationInDB(NotificationResponse):
    pass


# Schema para filtros
class NotificationFilter(BaseModel):
    type: Optional[str] = None
    priority: Optional[str] = None
    read_status: Optional[bool] = None
    action_required: Optional[bool] = None
    related_type: Optional[str] = None


# Schema para marcar como lida
class NotificationMarkRead(BaseModel):
    read_status: bool = True
