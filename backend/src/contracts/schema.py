"""
Schemas Pydantic para contratos
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, validator


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
    status: str = Field("active", pattern="^(active|expired|terminated)$")

    @validator("end_date")
    def end_date_after_start_date(cls, v, values):
        if "start_date" in values and v <= values["start_date"]:
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
    status: Optional[str] = Field(None, pattern="^(active|expired|terminated)$")


class ContractResponse(ContractBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
