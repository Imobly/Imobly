"""
Router para o módulo de dashboard
Endpoints de agregação (KPIs, Gráficos)
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.security import get_current_user_local_id
from .repository import DashboardRepository

router = APIRouter()


def get_dashboard_repository(db: Session = Depends(get_db)) -> DashboardRepository:
    """Dependency para obter repository do dashboard"""
    return DashboardRepository(db)


@router.get("/stats")
def get_dashboard_stats(
    user_id: int = Depends(get_current_user_local_id),
    repository: DashboardRepository = Depends(get_dashboard_repository),
) -> Dict[str, Any]:
    """
    Obter estatísticas completas do dashboard
    Inclui KPIs de propriedades, inquilinos e finanças
    """
    return repository.get_overview_stats(user_id)


@router.get("/properties/stats")
def get_property_stats(
    user_id: int = Depends(get_current_user_local_id),
    repository: DashboardRepository = Depends(get_dashboard_repository),
) -> Dict[str, Any]:
    """Obter estatísticas específicas de propriedades"""
    return repository.get_property_stats(user_id)


@router.get("/tenants/stats")
def get_tenant_stats(
    user_id: int = Depends(get_current_user_local_id),
    repository: DashboardRepository = Depends(get_dashboard_repository),
) -> Dict[str, Any]:
    """Obter estatísticas específicas de inquilinos"""
    return repository.get_tenant_stats(user_id)


@router.get("/financial/stats")
def get_financial_stats(
    user_id: int = Depends(get_current_user_local_id),
    repository: DashboardRepository = Depends(get_dashboard_repository),
) -> Dict[str, Any]:
    """Obter estatísticas financeiras"""
    return repository.get_financial_stats(user_id)


@router.get("/revenue/trend")
def get_revenue_trend(
    months: int = Query(12, ge=1, le=24, description="Número de meses para análise"),
    user_id: int = Depends(get_current_user_local_id),
    repository: DashboardRepository = Depends(get_dashboard_repository),
):
    """
    Obter tendência de receita mensal
    Mostra receitas, despesas e lucro por mês
    """
    return {
        "trend": repository.get_monthly_revenue_trend(user_id, months),
        "period_months": months
    }


@router.get("/overview")
def get_dashboard_overview(
    user_id: int = Depends(get_current_user_local_id),
    repository: DashboardRepository = Depends(get_dashboard_repository),
) -> Dict[str, Any]:
    """
    Endpoint principal do dashboard - visão geral completa
    """

    overview_stats = repository.get_overview_stats(user_id)
    revenue_trend = repository.get_monthly_revenue_trend(user_id, 6)
    
    return {
        **overview_stats,
        "revenue_trend": revenue_trend
    }
