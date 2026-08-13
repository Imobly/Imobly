"""
Schemas Pydantic para contratos
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class ContractBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    property_id: int
    tenant_id: int
    start_date: date
    end_date: date
    rent: Decimal = Field(..., ge=0)
    deposit: Decimal = Field(default=Decimal("0"), ge=0)
    interest_rate: Decimal = Field(default=Decimal("0"), ge=0)
    fine_rate: Decimal = Field(default=Decimal("0"), ge=0)
    due_day: Optional[int] = Field(None, ge=1, le=31, description="Dia do vencimento (1-31)")
    status: str = Field("ativo", pattern="^(ativo|inativo|expirado)$")

    # `@field_validator` substitui `@validator`, removido no Pydantic v3.
    # Em v2 os valores já validados ficam em `info.data`.
    @field_validator("end_date")
    @classmethod
    def end_date_after_start_date(cls, v: date, info: ValidationInfo) -> date:
        start_date = info.data.get("start_date")
        if start_date is not None and v <= start_date:
            raise ValueError("end_date deve ser posterior a start_date")
        return v


class ContractCreate(ContractBase):
    pass


class ContractCreateInternal(ContractBase):
    user_id: int


class ContractUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    property_id: Optional[int] = None
    tenant_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    rent: Optional[Decimal] = Field(None, ge=0)
    deposit: Optional[Decimal] = Field(None, ge=0)
    interest_rate: Optional[Decimal] = Field(None, ge=0)
    fine_rate: Optional[Decimal] = Field(None, ge=0)
    due_day: Optional[int] = Field(None, ge=1, le=31)
    status: Optional[str] = Field(None, pattern="^(ativo|inativo|expirado)$")


class ContractResponse(ContractBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
