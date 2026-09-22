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
from src.expenses.models import Expense
from src.contracts.models import Contract
from src.charges.models import Charge, PaymentEntry
from src.charges.repository import ChargeRepository

from src.core.tempo import hoje_brt

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
            .join(
                Contract,
                and_(Tenant.contract_id == Contract.id, Contract.user_id == user_id),
            )
            .filter(Tenant.user_id == user_id, Contract.status == "ativo")
            .scalar()
        ) or 0

        return {
            "total": total,
            "active": active,
            "inactive": total - active
        }

    def get_financial_stats(self, user_id: int) -> Dict[str, Any]:
        """
        KPIs financeiros.

        Receita é a soma dos RECEBIMENTOS do mês — dinheiro que entrou, com
        data própria. Antes era `SUM(payments.total_amount) WHERE status='pago'`,
        e essa coluna guardava ora o valor pago, ora o devido, conforme o
        caminho que criou a linha.

        A vencer e vencido saem do aging, ou seja, do SALDO de cada cobrança já
        com multa e juros do dia, e não do valor de face.
        """
        hoje = hoje_brt()
        current_month = hoje.month
        current_year = hoje.year

        monthly_income = (
            self.db.query(func.sum(PaymentEntry.amount))
            .filter(
                PaymentEntry.user_id == user_id,
                extract("month", PaymentEntry.date) == current_month,
                extract("year", PaymentEntry.date) == current_year,
            )
            .scalar()
            or Decimal("0")
        )

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

        baldes = ChargeRepository(self.db).aging(user_id, hoje=hoje)
        pending_payments = baldes["a_vencer"]["amount"]
        overdue_payments = sum(
            (dados["amount"] for nome, dados in baldes.items() if nome != "a_vencer"),
            Decimal("0"),
        )

        monthly_income = Decimal(str(monthly_income))
        return {
            "monthly_income": float(monthly_income),
            "monthly_expenses": float(monthly_expenses),
            "monthly_profit": float(monthly_income - monthly_expenses),
            "pending_payments": float(pending_payments),
            "overdue_payments": float(overdue_payments),
        }

    def get_monthly_revenue_trend(self, user_id: int, months: int = 12) -> list:
        """Obter tendência de receita mensal — 2 queries GROUP BY ao invés de 2×months queries em loop"""
        today = hoje_brt()

        # Calcular o primeiro dia do mês inicial do período
        start_month = today.month - months + 1
        start_year = today.year
        while start_month <= 0:
            start_month += 12
            start_year -= 1
        start_date = date(start_year, start_month, 1)

        # 1 query para receitas agrupadas por ano/mês — sobre os recebimentos,
        # que é onde a data e o valor do dinheiro que entrou realmente estão.
        revenue_rows = (
            self.db.query(
                extract("year", PaymentEntry.date).label("year"),
                extract("month", PaymentEntry.date).label("month"),
                func.sum(PaymentEntry.amount).label("total"),
            )
            .filter(
                PaymentEntry.user_id == user_id,
                PaymentEntry.date >= start_date,
            )
            .group_by(
                extract("year", PaymentEntry.date),
                extract("month", PaymentEntry.date),
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

        # Dinheiro efetivamente recebido no mês — um recebimento parcial entra
        # pelo valor que entrou, e não pelo valor cheio da cobrança.
        receitas_pagas = (
            self.db.query(func.sum(PaymentEntry.amount))
            .filter(
                PaymentEntry.user_id == user_id,
                extract("month", PaymentEntry.date) == current_month,
                extract("year", PaymentEntry.date) == current_year,
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

        # ── inadimplencia — a partir das cobranças, pelo SALDO ──
        # A versão anterior lia `Payment.total_amount` como "valor devido",
        # mas em registro parcial essa coluna guardava o valor PAGO: quem
        # pagasse 600 de 1.000 aparecia no painel devendo 600. Agora o número
        # é o saldo calculado — 400 mais multa e juros do dia.
        charge_repo = ChargeRepository(self.db)
        linhas = charge_repo.resumo_inadimplencia(user_id, hoje=today, limite=100)

        atrasados: List[Dict[str, Any]] = []
        parciais: List[Dict[str, Any]] = []
        for linha in linhas:
            item = {
                "tenant_id": linha["tenant_id"],
                "tenant_name": linha["tenant_name"],
                "property_id": linha["property_id"],
                "property_name": linha["property_name"],
                "amount": float(linha["balance"]),
                "due_date": linha["oldest_due_date"],
                "status": "atrasado" if linha["days_overdue"] > 0 else "parcial",
                "days_overdue": linha["days_overdue"],
                "situacao": linha["situacao"],
                "open_charges": linha["open_charges"],
            }
            # Uma linha por INQUILINO, não por cobrança. Quem deve três meses
            # aparecia três vezes e o operador somava de cabeça.
            (atrasados if item["days_overdue"] > 0 else parciais).append(item)

        inadimplencia = {
            "atrasados": atrasados,
            "parciais": parciais,
        }

        # ── aging — vencidos por faixa, o relatório padrão do setor ──
        baldes = charge_repo.aging(user_id, hoje=today)
        aging = {
            "a_vencer": float(baldes["a_vencer"]["amount"]),
            "d1_30": float(baldes["d1_30"]["amount"]),
            "d31_60": float(baldes["d31_60"]["amount"]),
            "d61_90": float(baldes["d61_90"]["amount"]),
            "d90_mais": float(baldes["d90_mais"]["amount"]),
        }
        total_em_aberto = sum(aging.values())
        total_vencido = total_em_aberto - aging["a_vencer"]

        return {
            "overview": overview,
            "financeiro": financeiro,
            "alertas_contratos": alertas_contratos,
            "inadimplencia": inadimplencia,
            "aging": {
                **aging,
                "total_open": total_em_aberto,
                "total_overdue": total_vencido,
            },
        }