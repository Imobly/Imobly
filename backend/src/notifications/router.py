"""
Router para o módulo de notificações
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.security import get_current_user_local_id
from .repository import NotificationRepository
from .schema import (
    NotificationCreate,
    NotificationCreateInternal,
    NotificationResponse,
    NotificationUpdate,
)

router = APIRouter()


def get_repo(db: Session = Depends(get_db)) -> NotificationRepository:
    return NotificationRepository(db)


# ─────────────────────────────────────────────────────────────
# Static routes — defined BEFORE /{notification_id} to avoid 405
# ─────────────────────────────────────────────────────────────

@router.get("/", response_model=List[NotificationResponse])
def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    read: Optional[bool] = Query(None, description="Filtrar por status de leitura"),
    type: Optional[str] = Query(None, description="Filtrar por tipo"),
    user_id: int = Depends(get_current_user_local_id),
    repo: NotificationRepository = Depends(get_repo),
):
    """Listar notificações com filtros opcionais"""
    return repo.get_by_user(user_id, skip=skip, limit=limit, read=read, type=type)


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    data: NotificationCreate,
    user_id: int = Depends(get_current_user_local_id),
    repo: NotificationRepository = Depends(get_repo),
):
    """Criar nova notificação"""
    internal = NotificationCreateInternal(**data.model_dump(), user_id=user_id)
    return repo.create(internal)


@router.get("/unread/", response_model=List[NotificationResponse])
def list_unread(
    user_id: int = Depends(get_current_user_local_id),
    repo: NotificationRepository = Depends(get_repo),
):
    """Listar apenas notificações não lidas"""
    return repo.get_unread(user_id)


@router.get("/count/unread/")
def count_unread(
    user_id: int = Depends(get_current_user_local_id),
    repo: NotificationRepository = Depends(get_repo),
):
    """Quantidade de notificações não lidas"""
    return {"unread_count": repo.count_unread(user_id)}


@router.put("/mark-all-read/")
def mark_all_as_read(
    user_id: int = Depends(get_current_user_local_id),
    repo: NotificationRepository = Depends(get_repo),
):
    """Marcar todas as notificações como lidas"""
    marked = repo.mark_all_as_read(user_id)
    return {"message": "Todas as notificações marcadas como lidas", "marked_as_read": marked}


@router.post("/process-background-tasks/")
def process_background_tasks(
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
):
    """
    Processar tarefas de background:
    - Atualizar status de pagamentos vencidos
    - Gerar notificações de contratos prestes a vencer
    - Gerar lembretes de pagamento
    """
    from datetime import date
    from src.payments.models import Payment
    from src.contracts.models import Contract

    today = date.today()

    # 1. Atualizar pagamentos vencidos
    pending_to_overdue = (
        db.query(Payment)
        .filter(
            Payment.user_id == user_id,
            Payment.status == "pending",
            Payment.due_date < today,
        )
        .update({"status": "overdue"}, synchronize_session=False)
    )
    db.commit()

    total_overdue = db.query(Payment).filter(Payment.user_id == user_id, Payment.status == "overdue").count()
    total_pending = db.query(Payment).filter(Payment.user_id == user_id, Payment.status == "pending").count()
    total_paid = db.query(Payment).filter(Payment.user_id == user_id, Payment.status == "paid").count()
    total_partial = db.query(Payment).filter(Payment.user_id == user_id, Payment.status == "partial").count()

    # 2. Notificações de contratos expirando em ≤30 dias
    from datetime import timedelta
    from .repository import NotificationRepository

    repo = NotificationRepository(db)
    expiring_threshold = today + timedelta(days=30)
    expiring_contracts = (
        db.query(Contract)
        .filter(
            Contract.user_id == user_id,
            Contract.status == "active",
            Contract.end_date <= expiring_threshold,
            Contract.end_date >= today,
        )
        .all()
    )

    contract_notifications = 0
    for contract in expiring_contracts:
        days_left = (contract.end_date - today).days
        # Avoid duplicate notifications (same contract, same day)
        existing = (
            db.query(__import__("src.notifications.models", fromlist=["Notification"]).Notification)
            .filter_by(
                user_id=user_id,
                type="contract_expiring",
                related_id=str(contract.id),
                date=today,
            )
            .first()
        )
        if not existing:
            repo.create(NotificationCreateInternal(
                user_id=user_id,
                type="contract_expiring",
                title=f"Contrato vence em {days_left} dias",
                message=f"O contrato #{contract.id} vence em {contract.end_date}.",
                date=today,
                priority="high" if days_left <= 7 else "medium",
                read_status=False,
                action_required=True,
                related_id=str(contract.id),
                related_type="contract",
            ))
            contract_notifications += 1

    # 3. Lembretes de pagamento (vencimento nos próximos 3 dias)
    reminder_threshold = today + timedelta(days=3)
    upcoming_payments = (
        db.query(Payment)
        .filter(
            Payment.user_id == user_id,
            Payment.status == "pending",
            Payment.due_date <= reminder_threshold,
            Payment.due_date >= today,
        )
        .all()
    )

    payment_reminders = 0
    for payment in upcoming_payments:
        days_left = (payment.due_date - today).days
        existing = (
            db.query(__import__("src.notifications.models", fromlist=["Notification"]).Notification)
            .filter_by(
                user_id=user_id,
                type="reminder",
                related_id=str(payment.id),
                date=today,
            )
            .first()
        )
        if not existing:
            repo.create(NotificationCreateInternal(
                user_id=user_id,
                type="reminder",
                title=f"Pagamento vence em {days_left} dia(s)",
                message=f"O pagamento #{payment.id} vence em {payment.due_date}.",
                date=today,
                priority="high" if days_left == 0 else "medium",
                read_status=False,
                action_required=True,
                related_id=str(payment.id),
                related_type="payment",
            ))
            payment_reminders += 1

    return {
        "payment_status_changes": {
            "pending_to_overdue": pending_to_overdue,
            "total_overdue": total_overdue,
            "total_pending": total_pending,
            "total_paid": total_paid,
            "total_partial": total_partial,
        },
        "contract_notifications": contract_notifications,
        "payment_reminders": payment_reminders,
        "overdue_notifications": 0,
    }


@router.delete("/cleanup/")
def cleanup_old_notifications(
    days: int = Query(30, ge=1),
    user_id: int = Depends(get_current_user_local_id),
    repo: NotificationRepository = Depends(get_repo),
):
    """Limpar notificações lidas mais antigas que N dias"""
    deleted = repo.delete_old(user_id, days=days)
    return {"message": f"Notificações antigas removidas", "deleted_count": deleted}


# ─────────────────────────────────────────────────────────────
# Parameterized routes
# ─────────────────────────────────────────────────────────────

@router.get("/{notification_id}/", response_model=NotificationResponse)
def get_notification(
    notification_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repo: NotificationRepository = Depends(get_repo),
):
    """Obter notificação por ID"""
    obj = repo.get_by_id_and_user(notification_id, user_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificação não encontrada")
    return obj


@router.put("/{notification_id}/read/", response_model=NotificationResponse)
def mark_as_read(
    notification_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repo: NotificationRepository = Depends(get_repo),
):
    """Marcar notificação como lida"""
    obj = repo.mark_as_read(notification_id, user_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificação não encontrada")
    return obj


@router.delete("/{notification_id}/")
def delete_notification(
    notification_id: int,
    user_id: int = Depends(get_current_user_local_id),
    repo: NotificationRepository = Depends(get_repo),
):
    """Deletar notificação"""
    if not repo.delete(notification_id, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificação não encontrada")
    return {"message": "Notificação deletada com sucesso"}
