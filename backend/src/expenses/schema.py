"""
Schemas para o módulo de despesas
"""

from datetime import date as DateType, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class ExpenseDocument(BaseModel):
    """Documento anexado a uma despesa"""
    id: str
    name: str
    type: str  # comprovante, nota_fiscal, recibo, outros
    url: str
    file_type: Optional[str] = None
    size: Optional[int] = None
    uploaded_at: Optional[str] = None


class ExpenseBase(BaseModel):
    user_id: Optional[int] = None
    type: str = Field(..., min_length=1, max_length=20, description="Tipo da despesa")
    property_id: int
    category: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    date: DateType = Field(..., description="Data da despesa")
    status: str = Field(..., pattern="^(pending|paid|overdue)$")
    priority: Optional[str] = Field(None, max_length=20)
    vendor: Optional[str] = Field(None, max_length=255)
    number: Optional[str] = Field(None, max_length=20)
    receipt: Optional[str] = None
    documents: Optional[List[ExpenseDocument]] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseCreateInternal(ExpenseBase):
    """Schema interno para criação com user_id"""
    user_id: int


class ExpenseUpdate(BaseModel):
    type: Optional[str] = Field(None, max_length=20)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    date: Optional[DateType] = Field(None, description="Data da despesa")
    status: Optional[str] = Field(None, pattern="^(pending|paid|overdue)$")
    priority: Optional[str] = Field(None, max_length=20)
    vendor: Optional[str] = Field(None, max_length=255)
    number: Optional[str] = Field(None, max_length=20)
    receipt: Optional[str] = None
    documents: Optional[List[ExpenseDocument]] = None
    notes: Optional[str] = None


class ExpenseRead(ExpenseBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpenseResponse(ExpenseRead):
    pass
