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
    """
    Uma linha por INQUILINO em débito — não por cobrança.

    `amount` é o SALDO devedor consolidado (já com multa e juros do dia), e não
    o valor de face: quem pagou 600 de 1.000 entra por 400 mais encargos.
    """
    tenant_id: int
    tenant_name: str
    property_id: int
    property_name: str
    amount: float
    due_date: date  # vencimento da cobrança mais antiga em aberto
    status: Literal["atrasado", "parcial"]
    days_overdue: int = 0
    situacao: str = "em_dia"  # em_dia | atraso_leve | inadimplente | critico
    open_charges: int = 0

    model_config = ConfigDict(from_attributes=True)


class InadimplenciaSection(BaseModel):
    """Listas de inadimplência divididas por tipo"""
    atrasados: List[InadimplenciaItem]
    parciais: List[InadimplenciaItem]


class AgingSection(BaseModel):
    """Saldo em aberto por faixa de atraso — o relatório padrão do setor."""
    a_vencer: float
    d1_30: float
    d31_60: float
    d61_90: float
    d90_mais: float
    total_open: float
    total_overdue: float


class DashboardSummaryResponse(BaseModel):
    """Resposta consolidada do GET /dashboard/summary"""
    overview: OverviewSection
    financeiro: FinanceiroSection
    alertas_contratos: AlertasContratosSection
    inadimplencia: InadimplenciaSection
    aging: AgingSection
