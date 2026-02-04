from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_id_from_token
from app.db.session import get_db
from app.src.contracts.models import Contract
from app.src.expenses.models import Expense
from app.src.payments.models import Payment
from app.src.payments.repository import PaymentRepository
from app.src.properties.models import Property
from app.src.properties.repository import PropertyRepository
from app.src.tenants.models import Tenant

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id_from_token)
):
    """Obter estatísticas básicas do dashboard (filtrado por usuário)"""

    # Contar propriedades do usuário
    total_properties = (
        db.query(func.count(Property.id)).filter(Property.user_id == user_id).scalar() or 0
    )

    # Contar inquilinos do usuário
    total_tenants = db.query(func.count(Tenant.id)).filter(Tenant.user_id == user_id).scalar() or 0

    # Contar contratos ativos do usuário
    total_contracts = (
        db.query(func.count(Contract.id))
        .filter(Contract.user_id == user_id, Contract.status == "active")
        .scalar()
        or 0
    )

    # Receita mensal (soma dos aluguéis de contratos ativos)
    monthly_revenue = (
        db.query(func.sum(Contract.rent))
        .filter(Contract.user_id == user_id, Contract.status == "active")
        .scalar()
        or 0.0
    )

    return {
        "total_properties": total_properties,
        "total_tenants": total_tenants,
        "total_contracts": total_contracts,
        "monthly_revenue": float(monthly_revenue),
    }


@router.get("/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id_from_token)
):
    """Obter resumo completo do dashboard (filtrado por usuário)"""

    payment_repo = PaymentRepository(db)

    # Contadores básicos
    total_properties = (
        db.query(func.count(Property.id)).filter(Property.user_id == user_id).scalar() or 0
    )

    active_contracts = (
        db.query(func.count(Contract.id))
        .filter(Contract.user_id == user_id, Contract.status == "active")
        .scalar()
        or 0
    )

    # Contratos vencendo em 30 dias
    expiring_date = date.today() + timedelta(days=30)
    expiring_soon = (
        db.query(func.count(Contract.id))
        .filter(
            Contract.user_id == user_id,
            Contract.status == "active",
            Contract.end_date <= expiring_date,
            Contract.end_date >= date.today(),
        )
        .scalar()
        or 0
    )

    # Receita mensal esperada (soma dos aluguéis ativos)
    monthly_revenue = (
        db.query(func.sum(Contract.rent))
        .filter(Contract.user_id == user_id, Contract.status == "active")
        .scalar()
        or 0.0
    )

    # Pagamentos em atraso
    overdue_payments = len(payment_repo.get_overdue_payments(db, user_id))

    # Pagamentos pendentes
    pending_payments = len(payment_repo.get_pending_payments(db, user_id))

    return {
        "properties": {"total": total_properties, "active_contracts": active_contracts},
        "contracts": {"active": active_contracts, "expiring_soon": expiring_soon},
        "financial": {
            "monthly_revenue": float(monthly_revenue),
            "overdue_payments": overdue_payments,
            "pending_payments": pending_payments,
        },
    }


@router.get("/revenue-chart")
async def get_revenue_chart(
    months: int = Query(default=12, ge=1, le=24),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id_from_token),
):
    """Obter dados para gráfico de receitas (filtrado por usuário)"""
    chart_data = []
    current_date = date.today()

    for i in range(months):
        target_date = current_date - timedelta(days=30 * i)
        month = target_date.month
        year = target_date.year

        # Primeiro e último dia do mês
        from calendar import monthrange

        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])

        # Somar pagamentos recebidos no mês
        revenue = (
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

        chart_data.append({"month": f"{year}-{month:02d}", "revenue": float(revenue)})

    return {"data": list(reversed(chart_data))}


@router.get("/property-performance")
async def get_property_performance(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id_from_token)
):
    """Obter performance das propriedades do usuário"""
    property_repo = PropertyRepository(db)

    # Buscar todas as propriedades do usuário
    properties = property_repo.get_by_user(db, user_id, skip=0, limit=1000)
    performance_data = []

    current_month = date.today().month
    current_year = date.today().year

    # Primeiro e último dia do mês
    from calendar import monthrange

    first_day = date(current_year, current_month, 1)
    last_day = date(current_year, current_month, monthrange(current_year, current_month)[1])

    for prop in properties:
        # Contar contratos ativos para esta propriedade
        active_contracts = (
            db.query(func.count(Contract.id))
            .filter(
                Contract.user_id == user_id,
                Contract.property_id == prop.id,
                Contract.status == "active",
            )
            .scalar()
            or 0
        )

        # Receita da propriedade no mês (pagamentos recebidos)
        revenue = (
            db.query(func.sum(Payment.amount))
            .filter(
                Payment.user_id == user_id,
                Payment.property_id == prop.id,
                Payment.status == "paid",
                Payment.payment_date >= first_day,
                Payment.payment_date <= last_day,
            )
            .scalar()
            or 0.0
        )

        # Receita esperada (soma dos aluguéis dos contratos ativos)
        expected_revenue = (
            db.query(func.sum(Contract.rent))
            .filter(
                Contract.user_id == user_id,
                Contract.property_id == prop.id,
                Contract.status == "active",
            )
            .scalar()
            or 0.0
        )

        performance_data.append(
            {
                "property_id": prop.id,
                "property_name": prop.name,
                "property_address": prop.address,
                "active_contracts": active_contracts,
                "revenue_received": float(revenue),
                "revenue_expected": float(expected_revenue),
                "collection_rate": round(
                    (revenue / expected_revenue * 100) if expected_revenue > 0 else 0, 2
                ),
            }
        )

    return {"properties": performance_data}


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id_from_token),
):
    """Obter atividades recentes do usuário"""

    # Pagamentos recentes (últimos 5)
    recent_payments = (
        db.query(Payment)
        .filter(Payment.user_id == user_id)
        .order_by(Payment.created_at.desc())
        .limit(limit // 2)
        .all()
    )

    # Contratos recentes (últimos 5)
    recent_contracts = (
        db.query(Contract)
        .filter(Contract.user_id == user_id)
        .order_by(Contract.created_at.desc())
        .limit(limit // 2)
        .all()
    )

    activities = []

    # Adicionar pagamentos
    for payment in recent_payments:
        activities.append(
            {
                "type": "payment",
                "description": f"Pagamento de R$ {payment.amount:.2f} - Status: {payment.status}",
                "date": str(payment.payment_date or payment.due_date),
                "related_id": payment.id,
                "created_at": str(payment.created_at)
                if hasattr(payment, "created_at")
                else str(payment.due_date),
            }
        )

    # Adicionar contratos
    for contract in recent_contracts:
        activities.append(
            {
                "type": "contract",
                "description": f"Contrato criado - Status: {contract.status}",
                "date": str(contract.start_date),
                "related_id": contract.id,
                "created_at": str(contract.created_at)
                if hasattr(contract, "created_at")
                else str(contract.start_date),
            }
        )

    # Ordenar por created_at se disponível, senão por date
    activities.sort(key=lambda x: x.get("created_at", x["date"]), reverse=True)

    return {"activities": activities[:limit]}


@router.get("/revenue-vs-expenses")
async def get_revenue_vs_expenses(
    months: int = Query(default=12, ge=1, le=24),
    property_id: Optional[int] = Query(
        default=None, description="Filtrar por propriedade específica"
    ),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id_from_token),
):
    """
    Obter dados comparativos de receitas vs despesas ao longo do tempo

    Retorna dados mensais de:
    - Receitas (pagamentos recebidos)
    - Despesas (todas as categorias)
    - Lucro líquido (receitas - despesas)

    Com opção de filtrar por propriedade específica
    """
    from calendar import monthrange

    chart_data = []
    current_date = date.today()

    for i in range(months):
        target_date = current_date - timedelta(days=30 * i)
        month = target_date.month
        year = target_date.year

        # Primeiro e último dia do mês
        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])

        # Query base de receitas (pagamentos recebidos)
        revenue_query = db.query(func.sum(Payment.amount)).filter(
            Payment.user_id == user_id,
            Payment.status == "paid",
            Payment.payment_date >= first_day,
            Payment.payment_date <= last_day,
        )

        # Query base de despesas
        expense_query = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user_id, Expense.date >= first_day, Expense.date <= last_day
        )

        # Aplicar filtro de propriedade se fornecido
        if property_id:
            revenue_query = revenue_query.filter(Payment.property_id == property_id)
            expense_query = expense_query.filter(Expense.property_id == property_id)

        revenue = revenue_query.scalar() or 0.0
        expenses = expense_query.scalar() or 0.0
        profit = float(revenue) - float(expenses)

        chart_data.append(
            {
                "month": f"{year}-{month:02d}",
                "revenue": float(revenue),
                "expenses": float(expenses),
                "profit": profit,
            }
        )

    return {"data": list(reversed(chart_data))}


@router.get("/financial-overview")
async def get_financial_overview(
    start_date: Optional[date] = Query(default=None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(default=None, description="Data final (YYYY-MM-DD)"),
    property_id: Optional[int] = Query(default=None, description="Filtrar por propriedade"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id_from_token),
):
    """
    Visão geral financeira com filtros de período e propriedade

    Retorna:
    - Total de receitas
    - Total de despesas
    - Lucro líquido
    - Breakdown por categoria de despesa
    - Status de pagamentos (pagos, pendentes, atrasados)
    """
    from calendar import monthrange

    # Se não fornecido, usar mês atual
    if not start_date or not end_date:
        current_month = date.today().month
        current_year = date.today().year
        start_date = date(current_year, current_month, 1)
        end_date = date(current_year, current_month, monthrange(current_year, current_month)[1])

    # Receitas no período
    revenue_query = db.query(func.sum(Payment.amount)).filter(
        Payment.user_id == user_id,
        Payment.status == "paid",
        Payment.payment_date >= start_date,
        Payment.payment_date <= end_date,
    )

    # Despesas no período
    expense_query = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id, Expense.date >= start_date, Expense.date <= end_date
    )

    # Aplicar filtro de propriedade
    if property_id:
        revenue_query = revenue_query.filter(Payment.property_id == property_id)
        expense_query = expense_query.filter(Expense.property_id == property_id)

    total_revenue = revenue_query.scalar() or 0.0
    total_expenses = expense_query.scalar() or 0.0

    # Breakdown de despesas por categoria
    expense_categories_query = db.query(
        Expense.category, func.sum(Expense.amount).label("total")
    ).filter(Expense.user_id == user_id, Expense.date >= start_date, Expense.date <= end_date)

    if property_id:
        expense_categories_query = expense_categories_query.filter(
            Expense.property_id == property_id
        )

    expense_breakdown = expense_categories_query.group_by(Expense.category).all()

    # Status dos pagamentos no período
    payments_query = db.query(Payment).filter(
        Payment.user_id == user_id, Payment.due_date >= start_date, Payment.due_date <= end_date
    )

    if property_id:
        payments_query = payments_query.filter(Payment.property_id == property_id)

    all_payments = payments_query.all()

    payment_stats = {
        "paid": len([p for p in all_payments if p.status == "paid"]),
        "pending": len([p for p in all_payments if p.status == "pending"]),
        "overdue": len([p for p in all_payments if p.status == "overdue"]),
        "partial": len([p for p in all_payments if p.status == "partial"]),
    }

    return {
        "period": {"start_date": str(start_date), "end_date": str(end_date)},
        "summary": {
            "total_revenue": float(total_revenue),
            "total_expenses": float(total_expenses),
            "net_profit": float(total_revenue) - float(total_expenses),
            "profit_margin": round(
                (
                    (float(total_revenue) - float(total_expenses))
                    / max(float(total_revenue), 1)
                    * 100
                ),
                2,
            ),
        },
        "expense_breakdown": [
            {"category": cat, "amount": float(total)} for cat, total in expense_breakdown
        ],
        "payment_status": payment_stats,
        "filters_applied": {"property_id": property_id},
    }


@router.get("/properties-status")
async def get_properties_status(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id_from_token)
):
    """
    Obter status de todos os imóveis do usuário

    Retorna para cada imóvel:
    - Informações básicas
    - Status de ocupação
    - Contratos ativos
    - Receita mensal esperada
    - Despesas do mês
    """
    from calendar import monthrange

    property_repo = PropertyRepository(db)
    properties = property_repo.get_by_user(db, user_id, skip=0, limit=1000)

    current_month = date.today().month
    current_year = date.today().year
    first_day = date(current_year, current_month, 1)
    last_day = date(current_year, current_month, monthrange(current_year, current_month)[1])

    properties_status = []

    for prop in properties:
        # Contratos ativos
        active_contracts = (
            db.query(Contract)
            .filter(
                Contract.user_id == user_id,
                Contract.property_id == prop.id,
                Contract.status == "active",
            )
            .all()
        )

        # Receita esperada (soma dos aluguéis)
        expected_revenue = sum(c.rent for c in active_contracts) if active_contracts else 0.0

        # Despesas do mês
        monthly_expenses = (
            db.query(func.sum(Expense.amount))
            .filter(
                Expense.user_id == user_id,
                Expense.property_id == prop.id,
                Expense.date >= first_day,
                Expense.date <= last_day,
            )
            .scalar()
            or 0.0
        )

        # Receita recebida do mês
        monthly_revenue = (
            db.query(func.sum(Payment.amount))
            .filter(
                Payment.user_id == user_id,
                Payment.property_id == prop.id,
                Payment.status == "paid",
                Payment.payment_date >= first_day,
                Payment.payment_date <= last_day,
            )
            .scalar()
            or 0.0
        )

        properties_status.append(
            {
                "id": prop.id,
                "name": prop.name,
                "address": prop.address,
                "type": prop.type,
                "status": "occupied" if active_contracts else "vacant",
                "active_contracts": len(active_contracts),
                "expected_monthly_revenue": float(expected_revenue),
                "received_monthly_revenue": float(monthly_revenue),
                "monthly_expenses": float(monthly_expenses),
                "net_profit": float(monthly_revenue) - float(monthly_expenses),
            }
        )

    # Estatísticas gerais
    total_properties = len(properties)
    occupied = len([p for p in properties_status if p["status"] == "occupied"])
    vacant = total_properties - occupied

    return {
        "summary": {
            "total_properties": total_properties,
            "occupied": occupied,
            "vacant": vacant,
            "occupancy_rate": round((occupied / max(total_properties, 1) * 100), 2),
        },
        "properties": properties_status,
    }
