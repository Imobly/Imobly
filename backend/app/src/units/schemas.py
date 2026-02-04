from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class UnitBase(BaseModel):
    property_id: int
    number: str = Field(..., min_length=1, max_length=50)
    area: Decimal = Field(..., gt=0)
    bedrooms: int = Field(..., ge=0)
    bathrooms: int = Field(..., ge=0)
    rent: Decimal = Field(..., gt=0)
    status: str = Field(..., pattern="^(vacant|occupied|maintenance)$")
    tenant: Optional[str] = None


class UnitCreate(UnitBase):
    pass


class UnitUpdate(BaseModel):
    number: Optional[str] = Field(None, min_length=1, max_length=50)
    area: Optional[Decimal] = Field(None, gt=0)
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[int] = Field(None, ge=0)
    rent: Optional[Decimal] = Field(None, gt=0)
    status: Optional[str] = Field(None, pattern="^(vacant|occupied|maintenance)$")
    tenant: Optional[str] = None


class UnitResponse(UnitBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Alias para Response
Unit = UnitResponse


class UnitInDB(UnitResponse):
    pass
