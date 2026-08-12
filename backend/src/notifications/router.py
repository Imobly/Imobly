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
    PaginatedNotifications,
)

router = APIRouter()


def get_repo(db: Session = Depends(get_db)) -> NotificationRepository:
    return NotificationRepository(db)


# ─────────────────────────────────────────────────────────────
# Static routes — defined BEFORE /{notification_id} to avoid 405
# ─────────────────────────────────────────────────────────────

@router.get("/", response_model=PaginatedNotifications)
def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    read: Optional[bool] = Query(None, description="Filtrar por status de leitura"),
    only_unread: bool = Query(False, description="Retornar apenas não lidas"),
    type: Optional[str] = Query(None, description="Filtrar por tipo"),
    user_id: int = Depends(get_current_user_local_id),
    repo: NotificationRepository = Depends(get_repo),
):
    """
    Listar notificações com paginação, ordenação (mais recentes primeiro)
    e filtro booleano only_unread.
    """
    items, total = repo.get_by_user(
        user_id, skip=skip, limit=limit, read=read,
        type=type, only_unread=only_unread,
    )
    return PaginatedNotifications(items=items, total=total, skip=skip, limit=limit)


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
    Processar tarefas de background manualmente:
    - Atualizar status de pagamentos vencidos
    - Gerar notificações de inadimplência
    - Gerar notificações de contratos prestes a vencer (30/60/90 dias)
    - Gerar lembretes de pagamento (próximos 3 dias)
    Usa lógica antispam (7 dias) e inclui metadata JSON.
    """
    from src.scheduler import run_background_checks

    return run_background_checks(db, user_id)


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
    notification_id: str,
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
    notification_id: str,
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
    notification_id: str,
    user_id: int = Depends(get_current_user_local_id),
    repo: NotificationRepository = Depends(get_repo),
):
    """Deletar notificação"""
    if not repo.delete(notification_id, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificação não encontrada")
    return {"message": "Notificação deletada com sucesso"}
