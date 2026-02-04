from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExpenseDocument(BaseModel):
    """Schema para documento/comprovante de despesa"""

    id: str
    name: str
    type: str  # 'comprovante', 'nota_fiscal', 'recibo', 'outros'
    url: str
    file_type: str  # 'pdf', 'jpg', 'png', etc
    size: int
    uploaded_at: str


class ExpenseBase(BaseModel):
    user_id: Optional[int] = None  # Optional for backwards compatibility, set from token in API
    type: str = Field(..., pattern="^(expense|maintenance)$")
    category: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    date: date_type
    property_id: int
    status: str = Field(..., pattern="^(pending|paid|scheduled)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    vendor: Optional[str] = Field(None, max_length=255)
    number: Optional[str] = Field(None, max_length=20, description="Telefone/contato do fornecedor")
    receipt: Optional[str] = None  # DEPRECATED - usar documents
    documents: Optional[List[Dict[str, Any]]] = Field(default_factory=list)  # Array de documentos


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    type: Optional[str] = Field(None, pattern="^(expense|maintenance)$")
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    date: Optional[date_type] = None
    status: Optional[str] = Field(None, pattern="^(pending|paid|scheduled)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    vendor: Optional[str] = Field(None, max_length=255)
    number: Optional[str] = Field(None, max_length=20, description="Telefone/contato do fornecedor")
    receipt: Optional[str] = None  # DEPRECATED
    documents: Optional[List[Dict[str, Any]]] = None


class ExpenseResponse(ExpenseBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Alias para Response
Expense = ExpenseResponse


class ExpenseInDB(Expense):
    pass


# Schema para filtros
class ExpenseFilter(BaseModel):
    type: Optional[str] = None
    category: Optional[str] = None
    property_id: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    date_from: Optional[date_type] = None
    date_to: Optional[date_type] = None
    vendor: Optional[str] = None


# Schema para categorias
class ExpenseCategory(BaseModel):
    name: str
    description: Optional[str] = None
