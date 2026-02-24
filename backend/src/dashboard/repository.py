"""
Repository para operações do dashboard (KPIs e agregações)
"""

from typing import Dict, Any
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

# Importar os models dos outros módulos
from src.properties.models import Property
from src.tenants.models import Tenant  
from src.payments.models import Payment
from src.expenses.models import Expense


class DashboardRepository:
    """Repository para consultas de dashboard e KPIs"""

    def __init__(self, db: Session):
        self.db = db

    def get_property_stats(self, user_id: int) -> Dict[str, Any]:
        """Obter estatísticas de propriedades"""
        total_properties = self.db.query(func.count(Property.id)).filter(
            Property.user_id == user_id
        ).scalar() or 0

        vacant_properties = self.db.query(func.count(Property.id)).filter(
            Property.user_id == user_id,
            Property.status == "vacant"
        ).scalar() or 0

        occupied_properties = self.db.query(func.count(Property.id)).filter(
            Property.user_id == user_id,
            Property.status == "occupied"
        ).scalar() or 0

        maintenance_properties = self.db.query(func.count(Property.id)).filter(
            Property.user_id == user_id,
            Property.status == "maintenance"
        ).scalar() or 0

        return {
            "total": total_properties,
            "vacant": vacant_properties,
            "occupied": occupied_properties,
            "maintenance": maintenance_properties,
            "occupancy_rate": (occupied_properties / total_properties * 100) if total_properties > 0 else 0
        }

    def get_tenant_stats(self, user_id: int) -> Dict[str, Any]:
        """Obter estatísticas de inquilinos"""
        total_tenants = self.db.query(func.count(Tenant.id)).filter(
            Tenant.user_id == user_id
        ).scalar() or 0

        active_tenants = self.db.query(func.count(Tenant.id)).filter(
            Tenant.user_id == user_id,
            Tenant.status == "active"
        ).scalar() or 0

        inactive_tenants = self.db.query(func.count(Tenant.id)).filter(
            Tenant.user_id == user_id,
            Tenant.status == "inactive"
        ).scalar() or 0

        return {
            "total": total_tenants,
            "active": active_tenants,
            "inactive": inactive_tenants
        }

    def get_financial_stats(self, user_id: int) -> Dict[str, Any]:
        """Obter estatísticas financeiras"""
        current_month = date.today().month
        current_year = date.today().year

        # Recebimentos do mês
        monthly_income = self.db.query(func.sum(Payment.total_amount)).filter(
            Payment.user_id == user_id,
            Payment.status == "paid",
            extract('month', Payment.payment_date) == current_month,
            extract('year', Payment.payment_date) == current_year
        ).scalar() or Decimal('0')

        # Despesas do mês
        monthly_expenses = self.db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            extract('month', Expense.date) == current_month,
            extract('year', Expense.date) == current_year
        ).scalar() or Decimal('0')

        # Pagamentos pendentes
        pending_payments = self.db.query(func.sum(Payment.total_amount)).filter(
            Payment.user_id == user_id,
            Payment.status == "pending"
        ).scalar() or Decimal('0')

        # Pagamentos em atraso
        overdue_payments = self.db.query(func.sum(Payment.total_amount)).filter(
            Payment.user_id == user_id,
            Payment.status == "overdue"
        ).scalar() or Decimal('0')

        return {
            "monthly_income": float(monthly_income),
            "monthly_expenses": float(monthly_expenses),
            "monthly_profit": float(monthly_income - monthly_expenses),
            "pending_payments": float(pending_payments),
            "overdue_payments": float(overdue_payments)
        }

    def get_monthly_revenue_trend(self, user_id: int, months: int = 12) -> list:
        """Obter tendência de receita mensal"""
        current_date = date.today()
        results = []

        for i in range(months):
            # Calcular mês e ano
            month = current_date.month - i
            year = current_date.year
            
            if month <= 0:
                month += 12
                year -= 1

            # Buscar receita do mês
            revenue = self.db.query(func.sum(Payment.total_amount)).filter(
                Payment.user_id == user_id,
                Payment.status == "paid",
                extract('month', Payment.payment_date) == month,
                extract('year', Payment.payment_date) == year
            ).scalar() or Decimal('0')

            # Buscar despesas do mês
            expenses = self.db.query(func.sum(Expense.amount)).filter(
                Expense.user_id == user_id,
                extract('month', Expense.date) == month,
                extract('year', Expense.date) == year
            ).scalar() or Decimal('0')

            results.append({
                "month": month,
                "year": year,
                "revenue": float(revenue),
                "expenses": float(expenses),
                "profit": float(revenue - expenses)
            })

        return sorted(results, key=lambda x: (x["year"], x["month"]))

    def get_overview_stats(self, user_id: int) -> Dict[str, Any]:
        """Obter estatísticas gerais do dashboard"""
        property_stats = self.get_property_stats(user_id)
        tenant_stats = self.get_tenant_stats(user_id)
        financial_stats = self.get_financial_stats(user_id)

        return {
            "properties": property_stats,
            "tenants": tenant_stats,
            "financial": financial_stats,
            "updated_at": datetime.utcnow().isoformat()
        }