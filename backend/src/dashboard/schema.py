"""
Schemas Pydantic para o módulo de dashboard — endpoint /summary
"""

from datetime import date
from typing import List, Literal

from pydantic import BaseModel, ConfigDict


class OverviewSection(BaseModel):
    """Contratos ativos/inativos e taxa de ocupação"""
    active_contracts: int
    inactive_contracts: int
    occupancy_rate: float  # 0-100


class FinanceiroSection(BaseModel):
    """Receitas, despesas e saldo do mês atual"""
    receitas_pagas: float
    despesas_pagas: float
    saldo: float


class AlertasContratosSection(BaseModel):
    """Contagem de contratos vencendo em 30/60/90 dias"""
    vencendo_30d: int
    vencendo_60d: int
    vencendo_90d: int


class InadimplenciaItem(BaseModel):
    """Inquilino com pagamento atrasado ou parcial"""
    tenant_id: int
    tenant_name: str
    property_id: int
    property_name: str
    amount: float
    due_date: date
    status: Literal["overdue", "partial"]

    model_config = ConfigDict(from_attributes=True)


class InadimplenciaSection(BaseModel):
    """Listas de inadimplência divididas por tipo"""
    atrasados: List[InadimplenciaItem]
    parciais: List[InadimplenciaItem]


class DashboardSummaryResponse(BaseModel):
    """Resposta consolidada do GET /dashboard/summary"""
    overview: OverviewSection
    financeiro: FinanceiroSection
    alertas_contratos: AlertasContratosSection
    inadimplencia: InadimplenciaSection
