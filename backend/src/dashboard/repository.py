"""
Repository para operações do dashboard (KPIs e agregações)
"""

from typing import Dict, Any, List
from decimal import Decimal
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, case

# Importar os models dos outros módulos
from src.properties.models import Property
from src.tenants.models import Tenant  
from src.payments.models import Payment
from src.expenses.models import Expense
from src.contracts.models import Contract

BRT = ZoneInfo("America/Sao_Paulo")


class DashboardRepository:
    """Repository para consultas de dashboard e KPIs"""

    def __init__(self, db: Session):
        self.db = db

    def get_property_stats(self, user_id: int) -> Dict[str, Any]:
        """Obter estatísticas de propriedades — 1 query GROUP BY"""
        rows = (
            self.db.query(Property.status, func.count(Property.id).label("count"))
            .filter(Property.user_id == user_id)
            .group_by(Property.status)
            .all()
        )
        counts = {status: cnt for status, cnt in rows}
        total = sum(counts.values())
        occupied = counts.get("occupied", 0)

        return {
            "total": total,
            "vacant": counts.get("vacant", 0),
            "occupied": occupied,
            "maintenance": counts.get("maintenance", 0),
            "occupancy_rate": (occupied / total * 100) if total > 0 else 0
        }

    def get_tenant_stats(self, user_id: int) -> Dict[str, Any]:
        """Obter estatísticas de inquilinos — derivado do contrato"""
        total = (
            self.db.query(func.count(Tenant.id))
            .filter(Tenant.user_id == user_id)
            .scalar()
        ) or 0

        active = (
            self.db.query(func.count(Tenant.id))
            .join(Contract, Tenant.contract_id == Contract.id)
            .filter(Tenant.user_id == user_id, Contract.status == "ativo")
            .scalar()
        ) or 0

        return {
            "total": total,
            "active": active,
            "inactive": total - active
        }

    def get_financial_stats(self, user_id: int) -> Dict[str, Any]:
        """Obter estatísticas financeiras — 2 queries ao invés de 4"""
        current_month = date.today().month
        current_year = date.today().year

        # Uma única query com agregação condicional para os três KPIs de pagamento
        result = (
            self.db.query(
                func.sum(
                    case(
                        (
                            and_(
                                Payment.status == "pago",
                                extract("month", Payment.payment_date) == current_month,
                                extract("year", Payment.payment_date) == current_year,
                            ),
                            Payment.total_amount,
                        ),
                        else_=0,
                    )
                ).label("monthly_income"),
                func.sum(
                    case(
                        (Payment.status == "pendente", Payment.total_amount),
                        else_=0,
                    )
                ).label("pending_payments"),
                func.sum(
                    case(
                        (Payment.status == "atrasado", Payment.total_amount),
                        else_=0,
                    )
                ).label("overdue_payments"),
            )
            .filter(Payment.user_id == user_id)
            .first()
        )

        # Despesas do mês (tabela separada — mantemos 1 query)
        monthly_expenses = (
            self.db.query(func.sum(Expense.amount))
            .filter(
                Expense.user_id == user_id,
                extract("month", Expense.date) == current_month,
                extract("year", Expense.date) == current_year,
            )
            .scalar()
            or Decimal("0")
        )

        monthly_income = Decimal(str(result.monthly_income or 0))
        pending_payments = Decimal(str(result.pending_payments or 0))
        overdue_payments = Decimal(str(result.overdue_payments or 0))

        return {
            "monthly_income": float(monthly_income),
            "monthly_expenses": float(monthly_expenses),
            "monthly_profit": float(monthly_income - monthly_expenses),
            "pending_payments": float(pending_payments),
            "overdue_payments": float(overdue_payments),
        }

    def get_monthly_revenue_trend(self, user_id: int, months: int = 12) -> list:
        """Obter tendência de receita mensal — 2 queries GROUP BY ao invés de 2×months queries em loop"""
        today = date.today()

        # Calcular o primeiro dia do mês inicial do período
        start_month = today.month - months + 1
        start_year = today.year
        while start_month <= 0:
            start_month += 12
            start_year -= 1
        start_date = date(start_year, start_month, 1)

        # 1 query para receitas agrupadas por ano/mês
        revenue_rows = (
            self.db.query(
                extract("year", Payment.payment_date).label("year"),
                extract("month", Payment.payment_date).label("month"),
                func.sum(Payment.total_amount).label("total"),
            )
            .filter(
                Payment.user_id == user_id,
                Payment.status == "pago",
                Payment.payment_date >= start_date,
            )
            .group_by(
                extract("year", Payment.payment_date),
                extract("month", Payment.payment_date),
            )
            .all()
        )

        # 1 query para despesas agrupadas por ano/mês
        expense_rows = (
            self.db.query(
                extract("year", Expense.date).label("year"),
                extract("month", Expense.date).label("month"),
                func.sum(Expense.amount).label("total"),
            )
            .filter(
                Expense.user_id == user_id,
                Expense.date >= start_date,
            )
            .group_by(
                extract("year", Expense.date),
                extract("month", Expense.date),
            )
            .all()
        )

        # Lookup rápido por (ano, mês)
        revenue_map = {(int(r.year), int(r.month)): float(r.total or 0) for r in revenue_rows}
        expense_map = {(int(r.year), int(r.month)): float(r.total or 0) for r in expense_rows}

        # Gerar lista completa de meses no período
        results = []
        for i in range(months):
            month = today.month - i
            year = today.year
            if month <= 0:
                month += 12
                year -= 1
            rev = revenue_map.get((year, month), 0.0)
            exp = expense_map.get((year, month), 0.0)
            results.append({
                "month": month,
                "year": year,
                "revenue": rev,
                "expenses": exp,
                "profit": rev - exp,
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
            "updated_at": datetime.now(BRT).isoformat()
        }

    # ────────────────────────────────────────────────────────────
    # GET /dashboard/summary — endpoint consolidado
    # ────────────────────────────────────────────────────────────

    def get_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Retorna objeto consolidado para o frontend:
        overview, financeiro, alertas_contratos, inadimplencia
        """
        today = datetime.now(BRT).date()

        # ── overview ──
        property_stats = self.get_property_stats(user_id)

        active_contracts = (
            self.db.query(func.count(Contract.id))
            .filter(Contract.user_id == user_id, Contract.status == "ativo")
            .scalar() or 0
        )
        inactive_contracts = (
            self.db.query(func.count(Contract.id))
            .filter(Contract.user_id == user_id, Contract.status.in_(["expirado", "inativo"]))
            .scalar() or 0
        )

        overview = {
            "active_contracts": active_contracts,
            "inactive_contracts": inactive_contracts,
            "occupancy_rate": property_stats.get("occupancy_rate", 0),
        }

        # ── financeiro (mês atual, fuso BRT) ──
        current_month = today.month
        current_year = today.year

        receitas_pagas = (
            self.db.query(func.sum(Payment.total_amount))
            .filter(
                Payment.user_id == user_id,
                Payment.status == "pago",
                extract("month", Payment.payment_date) == current_month,
                extract("year", Payment.payment_date) == current_year,
            )
            .scalar() or Decimal("0")
        )

        despesas_pagas = (
            self.db.query(func.sum(Expense.amount))
            .filter(
                Expense.user_id == user_id,
                extract("month", Expense.date) == current_month,
                extract("year", Expense.date) == current_year,
            )
            .scalar() or Decimal("0")
        )

        financeiro = {
            "receitas_pagas": float(receitas_pagas),
            "despesas_pagas": float(despesas_pagas),
            "saldo": float(Decimal(str(receitas_pagas)) - Decimal(str(despesas_pagas))),
        }

        # ── alertas_contratos — 1 query com CASE ──
        alertas = (
            self.db.query(
                func.count(case(
                    (Contract.end_date <= today + timedelta(days=30), Contract.id),
                )).label("d30"),
                func.count(case(
                    (and_(
                        Contract.end_date > today + timedelta(days=30),
                        Contract.end_date <= today + timedelta(days=60),
                    ), Contract.id),
                )).label("d60"),
                func.count(case(
                    (and_(
                        Contract.end_date > today + timedelta(days=60),
                        Contract.end_date <= today + timedelta(days=90),
                    ), Contract.id),
                )).label("d90"),
            )
            .filter(
                Contract.user_id == user_id,
                Contract.status == "ativo",
                Contract.end_date >= today,
                Contract.end_date <= today + timedelta(days=90),
            )
            .first()
        )

        alertas_contratos = {
            "vencendo_30d": alertas.d30 if alertas else 0,
            "vencendo_60d": alertas.d60 if alertas else 0,
            "vencendo_90d": alertas.d90 if alertas else 0,
        }

        # ── inadimplencia — JOIN Payment + Tenant + Property ──
        delinquent_rows = (
            self.db.query(
                Payment.tenant_id,
                Tenant.name.label("tenant_name"),
                Payment.property_id,
                Property.name.label("property_name"),
                Payment.total_amount.label("amount"),
                Payment.due_date,
                Payment.status,
            )
            .join(Tenant, Payment.tenant_id == Tenant.id)
            .join(Property, Payment.property_id == Property.id)
            .filter(
                Payment.user_id == user_id,
                Payment.status.in_(["atrasado", "parcial"]),
            )
            .order_by(Payment.due_date.asc())
            .all()
        )

        atrasados: List[Dict[str, Any]] = []
        parciais: List[Dict[str, Any]] = []
        for row in delinquent_rows:
            item = {
                "tenant_id": row.tenant_id,
                "tenant_name": row.tenant_name,
                "property_id": row.property_id,
                "property_name": row.property_name,
                "amount": float(row.amount),
                "due_date": row.due_date,
                "status": row.status,
            }
            if row.status == "atrasado":
                atrasados.append(item)
            else:
                parciais.append(item)

        inadimplencia = {
            "atrasados": atrasados,
            "parciais": parciais,
        }

        return {
            "overview": overview,
            "financeiro": financeiro,
            "alertas_contratos": alertas_contratos,
            "inadimplencia": inadimplencia,
        }