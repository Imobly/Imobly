from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_id_from_token
from app.db.session import get_db

from .controller import notification_controller
from .models import Notification
from .schemas import NotificationCreate, NotificationResponse, NotificationUpdate

router = APIRouter()


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification: NotificationCreate,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Criar nova notificação manualmente"""
    return notification_controller(db).create_notification(db, notification)


@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False,
    type: Optional[str] = None,
    priority: Optional[str] = None,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    Listar notificações do usuário

    Query params:
    - unread_only: Apenas não lidas
    - type: Filtrar por tipo
    - priority: Filtrar por prioridade
    """
    query = db.query(Notification).filter(Notification.user_id == user_id)

    if unread_only:
        query = query.filter(Notification.read_status.is_(False))

    if type:
        query = query.filter(Notification.type == type)

    if priority:
        query = query.filter(Notification.priority == priority)

    return query.order_by(Notification.date.desc()).offset(skip).limit(limit).all()


@router.get("/unread", response_model=List[NotificationResponse])
async def get_unread_notifications(
    limit: int = 50,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Buscar apenas notificações não lidas"""
    from app.core.notification_service import NotificationService

    return NotificationService.get_unread_notifications(db, user_id, limit)


@router.get("/count/unread")
async def count_unread_notifications(
    user_id: int = Depends(get_current_user_id_from_token), db: Session = Depends(get_db)
):
    """Contar notificações não lidas"""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read_status.is_(False))
        .count()
    )

    return {"unread_count": count}


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: str,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Marcar notificação como lida"""
    from app.core.notification_service import NotificationService

    notification = NotificationService.mark_as_read(db, notification_id, user_id)

    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    return notification


@router.put("/mark-all-read")
async def mark_all_notifications_as_read(
    user_id: int = Depends(get_current_user_id_from_token), db: Session = Depends(get_db)
):
    """Marcar todas as notificações como lidas"""
    from app.core.notification_service import NotificationService

    count = NotificationService.mark_all_as_read(db, user_id)
    return {"marked_as_read": count}


@router.delete("/cleanup")
async def cleanup_old_notifications(
    days_old: int = Query(90, ge=30, le=365),
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Deletar notificações lidas antigas"""
    from app.core.notification_service import NotificationService

    count = NotificationService.delete_old_notifications(db, user_id, days_old)
    return {"deleted_count": count}


@router.post("/process-background-tasks")
async def process_background_tasks(
    user_id: int = Depends(get_current_user_id_from_token), db: Session = Depends(get_db)
):
    """
    Processar todas as tarefas de background

    Este endpoint:
    - Atualiza status de pagamentos automaticamente
    - Gera notificações de contratos vencendo
    - Gera lembretes de pagamento
    - Gera notificações de atraso
    """
    from app.core.background_tasks import BackgroundTasksService

    results = BackgroundTasksService.run_all_background_tasks(db, user_id)
    return results


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Obter notificação por ID"""
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )

    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    return notification


@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: str,
    notification_update: NotificationUpdate,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Atualizar notificação"""
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )

    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    return notification_controller(db).update_notification(db, notification_id, notification_update)


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Deletar notificação"""
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )

    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    return notification_controller(db).delete_notification(db, notification_id)
