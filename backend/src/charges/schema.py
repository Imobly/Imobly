"""
Schemas Pydantic para cobranças e recebimentos.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

_METODO_PATTERN = "^(pix|boleto|transferencia|dinheiro|cartao_credito|cartao_debito|cash|transfer|check|card|outro)$"
_STATUS_PATTERN = "^(aberta|parcial|vencida|quitada|cancelada)$"


class ChargeBase(BaseModel):
    contract_id: int
    property_id: Optional[int] = None
    tenant_id: Optional[int] = None
    competencia: date
    due_date: date
    rent_amount: Decimal = Field(..., gt=0)
    charges_amount: Decimal = Field(default=Decimal("0"), ge=0)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)
    description: Optional[str] = None


class ChargeCreate(ChargeBase):
    """
    Criação manual de cobrança (avulsa, fora da geração mensal).

    Repare que NÃO existe `status` aqui, nem em `ChargeUpdate`: o status é
    derivado do saldo. Deixá-lo entrar pelo payload foi o que permitiu, no
    modelo antigo, gravar "pago" numa cobrança sem nenhum recebimento por trás.
    As taxas também não vêm do cliente — são copiadas do contrato na emissão.
    """


class ChargeUpdate(BaseModel):
    due_date: Optional[date] = None
    rent_amount: Optional[Decimal] = Field(None, gt=0)
    charges_amount: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None


class PaymentEntryCreate(BaseModel):
    """Registro de um recebimento aplicado a uma cobrança."""

    date: date
    amount: Decimal = Field(..., gt=0)
    method: Optional[str] = Field(None, pattern=_METODO_PATTERN)
    description: Optional[str] = None


class PaymentEntryRead(PaymentEntryCreate):
    id: int
    charge_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChargePosition(BaseModel):
    """A posição calculada — o que o painel realmente consome."""

    base_amount: Decimal
    fine_amount: Decimal
    interest_amount: Decimal
    total_due: Decimal
    paid_amount: Decimal
    balance: Decimal
    days_overdue: int
    aging_bucket: str
    reference_date: date
    settled_at: Optional[date] = None


class ChargeRead(BaseModel):
    id: int
    user_id: int
    contract_id: int
    property_id: int
    tenant_id: int
    competencia: date
    due_date: date
    rent_amount: Decimal
    charges_amount: Decimal
    discount_amount: Decimal
    fine_rate: Decimal
    interest_rate: Decimal
    status: str
    description: Optional[str] = None
    canceled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChargeDetail(ChargeRead):
    """Cobrança + posição + recebimentos. Resposta do GET /charges/{id}."""

    position: ChargePosition
    entries: List[PaymentEntryRead] = []
    tenant_name: Optional[str] = None
    property_name: Optional[str] = None


class ChargeListItem(ChargeRead):
    """Item de lista: traz a posição, mas não a lista de recebimentos."""

    position: ChargePosition
    tenant_name: Optional[str] = None
    property_name: Optional[str] = None


class GenerateChargesRequest(BaseModel):
    """
    Geração das cobranças de uma competência.

    `competencia` omitida significa o mês corrente. A operação é idempotente
    por (contrato, competência) — rodar duas vezes não duplica nada.
    """

    competencia: Optional[date] = None
    contract_id: Optional[int] = None


class GenerateChargesResponse(BaseModel):
    competencia: date
    created: int
    skipped_existing: int
    skipped_no_due_day: int
    charge_ids: List[int]


class AgingBucket(BaseModel):
    bucket: str
    label: str
    count: int
    amount: Decimal


class AgingReport(BaseModel):
    """Relatório de vencidos por faixa — o relatório padrão de inadimplência."""

    as_of: date
    buckets: List[AgingBucket]
    total_open: Decimal
    total_overdue: Decimal


class TenantLedgerEntry(BaseModel):
    charge_id: int
    competencia: date
    due_date: date
    property_id: int
    property_name: Optional[str] = None
    status: str
    position: ChargePosition


class TenantLedger(BaseModel):
    """Extrato e situação financeira de um inquilino."""

    tenant_id: int
    tenant_name: str
    as_of: date
    situacao: str  # em_dia | atraso_leve | inadimplente | critico
    open_balance: Decimal
    overdue_balance: Decimal
    oldest_overdue_days: int
    open_charges: int
    # Histórico — o que decide renovação de contrato.
    charges_settled: int
    settled_on_time: int
    on_time_rate: float  # 0-100
    average_delay_days: float
    entries: List[TenantLedgerEntry] = []
