"""
Schemas para o módulo de pagamentos
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# Payment method values sent by the frontend UI
_PAYMENT_METHOD_PATTERN = "^(pix|boleto|transferencia|dinheiro|cartao_credito|cartao_debito|cash|transfer|check|card|outro)$"


class PaymentBase(BaseModel):
    user_id: Optional[int] = None
    property_id: int
    tenant_id: int
    contract_id: int
    due_date: date
    payment_date: Optional[date] = None
    amount: Decimal = Field(..., gt=0)
    # `Decimal("0")`, não `0`: o Pydantic v2 não valida defaults, então um
    # int aqui saía como int na serialização de um campo monetário.
    fine_amount: Decimal = Field(default=Decimal("0"), ge=0)
    # Juros separados da multa: somados num campo só, a composição da cobrança
    # ficava impossível de auditar.
    interest_amount: Decimal = Field(default=Decimal("0"), ge=0)
    # `ge=0`, não `gt=0`: registrar uma cobrança em aberto (valor pago zero) é
    # caso de uso legítimo — e era, aliás, o único caminho capaz de produzir o
    # status "atrasado" que o próprio cálculo gera. Com `gt=0` a validação
    # falhava DENTRO do handler e virava 500 em vez de 201.
    total_amount: Decimal = Field(..., ge=0)
    status: str = Field(..., pattern="^(pendente|pago|atrasado|parcial)$")
    payment_method: Optional[str] = Field(None, pattern=_PAYMENT_METHOD_PATTERN)
    description: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentCreateInternal(PaymentBase):
    """Schema interno para criação com user_id"""
    user_id: int


class PaymentUpdate(BaseModel):
    payment_date: Optional[date] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    fine_amount: Optional[Decimal] = Field(None, ge=0)
    interest_amount: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern="^(pendente|pago|atrasado|parcial)$")
    payment_method: Optional[str] = Field(None, pattern=_PAYMENT_METHOD_PATTERN)
    description: Optional[str] = None


class PaymentCalculateRequest(BaseModel):
    contract_id: int
    due_date: date
    payment_date: Optional[date] = None
    paid_amount: Optional[Decimal] = Field(None, ge=0)


class PaymentRegisterRequest(BaseModel):
    contract_id: int
    property_id: Optional[int] = None
    tenant_id: Optional[int] = None
    due_date: date
    payment_date: date
    paid_amount: Decimal = Field(..., ge=0)
    payment_method: Optional[str] = Field(None, pattern=_PAYMENT_METHOD_PATTERN)
    description: Optional[str] = None


class BulkConfirmRequest(BaseModel):
    payment_ids: List[int] = Field(..., min_length=1)
    payment_date: Optional[date] = None


class PaymentRead(PaymentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentResponse(PaymentRead):
    pass
