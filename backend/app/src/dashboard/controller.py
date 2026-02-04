from calendar import monthrange
from datetime import date
from typing import Any, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.src.contracts.models import Contract
from app.src.contracts.repository import ContractRepository
from app.src.payments.models import Payment
from app.src.payments.repository import PaymentRepository
from app.src.properties.models import Property
from app.src.properties.repository import PropertyRepository
from app.src.tenants.models import Tenant
from app.src.tenants.repository import TenantRepository


class DashboardController:
    """Controller para gerenciar operações do dashboard com multi-tenancy"""

    def __init__(self, db: Session):
        self.db = db
        self.property_repo = PropertyRepository(db)
        self.contract_repo = ContractRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.tenant_repo = TenantRepository(db)

    def get_overview(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Obter visão geral do dashboard (filtrado por usuário)"""
        # Contar propriedades do usuário
        total_properties = (
            db.query(func.count(Property.id)).filter(Property.user_id == user_id).scalar() or 0
        )

        # Contar inquilinos do usuário
        total_tenants = (
            db.query(func.count(Tenant.id)).filter(Tenant.user_id == user_id).scalar() or 0
        )

        # Contar contratos ativos do usuário
        active_contracts = (
            db.query(func.count(Contract.id))
            .filter(Contract.user_id == user_id, Contract.status == "active")
            .scalar()
            or 0
        )

        # Estatísticas de pagamentos
        pending_payments = len(self.payment_repo.get_pending_payments(db, user_id))
        overdue_payments = len(self.payment_repo.get_overdue_payments(db, user_id))

        return {
            "total_properties": total_properties,
            "total_tenants": total_tenants,
            "active_contracts": active_contracts,
            "pending_payments": pending_payments,
            "overdue_payments": overdue_payments,
            "occupancy_rate": (active_contracts / max(total_properties, 1)) * 100,
        }

    def get_financial_summary(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Obter resumo financeiro (filtrado por usuário)"""
        # Total de receitas esperadas (soma dos aluguéis dos contratos ativos)
        total_rent = (
            db.query(func.sum(Contract.rent))
            .filter(Contract.user_id == user_id, Contract.status == "active")
            .scalar()
            or 0.0
        )

        # Pagamentos recebidos no mês atual
        current_month = date.today().month
        current_year = date.today().year
        first_day = date(current_year, current_month, 1)
        last_day = date(current_year, current_month, monthrange(current_year, current_month)[1])

        payments_received = (
            db.query(func.sum(Payment.amount))
            .filter(
                Payment.user_id == user_id,
                Payment.status == "paid",
                Payment.payment_date >= first_day,
                Payment.payment_date <= last_day,
            )
            .scalar()
            or 0.0
        )

        # Inadimplência (soma dos pagamentos em atraso)
        overdue_amount = (
            db.query(func.sum(Payment.amount))
            .filter(
                Payment.user_id == user_id,
                Payment.status.in_(["pending", "partial"]),
                Payment.due_date < date.today(),
            )
            .scalar()
            or 0.0
        )

        return {
            "expected_monthly_revenue": float(total_rent),
            "payments_received": float(payments_received),
            "overdue_amount": float(overdue_amount),
            "collection_rate": (
                ((payments_received / max(total_rent, 1)) * 100) if total_rent > 0 else 0
            ),
        }

    def get_recent_activities(self, db: Session, user_id: int, limit: int = 5) -> Dict[str, Any]:
        """Obter atividades recentes do usuário"""
        # Contratos recentes
        recent_contracts = (
            db.query(Contract)
            .filter(Contract.user_id == user_id)
            .order_by(Contract.created_at.desc())
            .limit(limit)
            .all()
        )

        # Pagamentos recentes
        recent_payments = (
            db.query(Payment)
            .filter(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
            .all()
        )

        return {"recent_contracts": recent_contracts, "recent_payments": recent_payments}


# Controller class ready for use with multi-tenancy
