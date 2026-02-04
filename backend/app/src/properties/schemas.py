from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class PropertyBase(BaseModel):
    user_id: Optional[int] = None  # Optional for backwards compatibility, set from token in API
    name: str = Field(..., min_length=1, max_length=255)
    address: str = Field(..., min_length=1)
    neighborhood: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=50)
    zip_code: str = Field(..., min_length=1, max_length=20)
    type: str = Field(..., pattern="^(apartment|house|commercial|studio)$")
    area: Decimal = Field(..., gt=0)
    bedrooms: int = Field(..., ge=0)
    bathrooms: int = Field(..., ge=0)
    parking_spaces: int = Field(0, ge=0)
    rent: Decimal = Field(..., gt=0)
    status: str = Field("vacant", pattern="^(vacant|occupied|maintenance|inactive)$")
    description: Optional[str] = None
    images: Optional[List[str]] = []
    is_residential: bool = True
    tenant_id: Optional[int] = None


class PropertyCreate(PropertyBase):
    pass


class PropertyCreateInternal(PropertyBase):
    """Schema interno para criação com user_id"""

    user_id: int


class PropertyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = None
    neighborhood: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    type: Optional[str] = Field(None, pattern="^(apartment|house|commercial|studio)$")
    area: Optional[Decimal] = Field(None, gt=0)
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[int] = Field(None, ge=0)
    parking_spaces: Optional[int] = Field(None, ge=0)
    rent: Optional[Decimal] = Field(None, gt=0)
    status: Optional[str] = Field(None, pattern="^(vacant|occupied|maintenance|inactive)$")
    description: Optional[str] = None
    images: Optional[List[str]] = None
    is_residential: Optional[bool] = None
    tenant_id: Optional[int] = None


class PropertyResponse(PropertyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PropertyInDB(PropertyResponse):
    pass


# Schemas para filtros
class PropertyFilter(BaseModel):
    type: Optional[str] = None
    status: Optional[str] = None
    min_rent: Optional[Decimal] = None
    max_rent: Optional[Decimal] = None
    min_area: Optional[Decimal] = None
    max_area: Optional[Decimal] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None
    min_bathrooms: Optional[int] = None
    max_bathrooms: Optional[int] = None
