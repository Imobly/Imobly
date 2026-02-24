"""
Schemas Pydantic para o módulo de notificações
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

_TYPE_PATTERN = "^(contract_expiring|payment_overdue|maintenance_urgent|system_alert|reminder)$"
_PRIORITY_PATTERN = "^(low|medium|high|urgent)$"
_RELATED_TYPE_PATTERN = "^(contract|payment|maintenance|property)$"


class NotificationBase(BaseModel):
    type: str = Field(..., pattern=_TYPE_PATTERN)
    title: str
    message: str
    date: date
    priority: str = Field("medium", pattern=_PRIORITY_PATTERN)
    read_status: bool = False
    action_required: bool = False
    related_id: Optional[str] = None
    related_type: Optional[str] = Field(None, pattern=_RELATED_TYPE_PATTERN)


class NotificationCreate(NotificationBase):
    pass


class NotificationCreateInternal(NotificationBase):
    user_id: int


class NotificationUpdate(BaseModel):
    type: Optional[str] = Field(None, pattern=_TYPE_PATTERN)
    title: Optional[str] = None
    message: Optional[str] = None
    date: Optional[date] = None
    priority: Optional[str] = Field(None, pattern=_PRIORITY_PATTERN)
    read_status: Optional[bool] = None
    action_required: Optional[bool] = None
    related_id: Optional[str] = None
    related_type: Optional[str] = Field(None, pattern=_RELATED_TYPE_PATTERN)


class NotificationResponse(NotificationBase):
    # id is int in DB but the frontend TypeScript expects string
    id: str
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id_to_str(cls, v):
        return str(v)
