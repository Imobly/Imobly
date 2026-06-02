"""
Schemas Pydantic para o módulo de notificações
"""

from datetime import date as DateType, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

_TYPE_PATTERN = "^(contract_expiring|payment_overdue|partial_payment|payment_registered|maintenance_urgent|system_alert|reminder|tenant_delinquent)$"
_PRIORITY_PATTERN = "^(low|medium|high|urgent)$"
_RELATED_TYPE_PATTERN = "^(contract|payment|maintenance|property)$"


class NotificationBase(BaseModel):
    type: str = Field(..., pattern=_TYPE_PATTERN)
    title: str
    message: str
    date: DateType = Field(default_factory=DateType.today)
    priority: str = Field("medium", pattern=_PRIORITY_PATTERN)
    read_status: bool = False
    action_required: bool = False
    related_id: Optional[str] = None
    related_type: Optional[str] = Field(None, pattern=_RELATED_TYPE_PATTERN)
    link: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    pass


class NotificationCreateInternal(NotificationBase):
    user_id: int


class NotificationUpdate(BaseModel):
    type: Optional[str] = Field(None, pattern=_TYPE_PATTERN)
    title: Optional[str] = None
    message: Optional[str] = None
    date: Optional[DateType] = None
    priority: Optional[str] = Field(None, pattern=_PRIORITY_PATTERN)
    read_status: Optional[bool] = None
    action_required: Optional[bool] = None
    related_id: Optional[str] = None
    related_type: Optional[str] = Field(None, pattern=_RELATED_TYPE_PATTERN)
    link: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationResponse(NotificationBase):
    # id is int in DB but the frontend TypeScript expects string
    id: str
    user_id: int
    created_at: datetime
    updated_at: datetime

    # No ORM, o atributo se chama 'notification_metadata' (metadata é reservado).
    # validation_alias faz o Pydantic ler de 'notification_metadata' ao usar from_attributes,
    # mas serializar como 'metadata' (nome do campo) na resposta JSON.
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias="notification_metadata")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id_to_str(cls, v):
        return str(v)


class PaginatedNotifications(BaseModel):
    """Resposta paginada de notificações"""
    items: List[NotificationResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)
