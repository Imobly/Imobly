"""
Schemas para o módulo de inquilinos (tenants)
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmergencyContact(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=1, max_length=20)
    relationship: str = Field(..., min_length=1, max_length=100)


class TenantDocument(BaseModel):
    id: str
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(
        ..., pattern="^(rg|cpf|cnh|comprovante_residencia|comprovante_renda|contrato|outros)$"
    )
    url: str


class TenantBase(BaseModel):
    user_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=20)
    cpf_cnpj: str = Field(..., min_length=1, max_length=20)
    birth_date: Optional[date] = None
    profession: str = Field(..., min_length=1, max_length=100)
    emergency_contact: Optional[EmergencyContact] = None
    documents: Optional[List[TenantDocument]] = []
    contract_id: Optional[int] = None


class TenantCreate(TenantBase):
    pass


class TenantCreateInternal(TenantBase):
    """Schema interno para criação com user_id"""
    user_id: int


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=1, max_length=20)
    cpf_cnpj: Optional[str] = Field(None, min_length=1, max_length=20)
    birth_date: Optional[date] = None
    profession: Optional[str] = Field(None, max_length=100)
    emergency_contact: Optional[EmergencyContact] = None
    documents: Optional[List[TenantDocument]] = None
    contract_id: Optional[int] = None


class TenantRead(TenantBase):
    id: int
    created_at: datetime
    updated_at: datetime

    # Derivado do contrato vinculado, não armazenado (a coluna `tenants.status`
    # foi removida). Sem este campo na resposta, o frontend lia `undefined` e
    # exibia TODO inquilino como "inativo".
    status: str = "inativo"

    model_config = ConfigDict(from_attributes=True)


class TenantResponse(TenantRead):
    pass