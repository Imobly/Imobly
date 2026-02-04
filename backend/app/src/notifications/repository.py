from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository

from .models import Notification
from .schemas import NotificationCreate, NotificationUpdate


class NotificationRepository(BaseRepository[Notification, NotificationCreate, NotificationUpdate]):
    """Repository para operações com notificações"""

    def __init__(self, db: Session):
        super().__init__(Notification)
        self.db = db

    def get_by_type(self, db: Session, notification_type: str) -> List[Notification]:
        """Buscar notificações por tipo"""
        return db.query(Notification).filter(Notification.type == notification_type).all()

    def get_by_priority(self, db: Session, priority: str) -> List[Notification]:
        """Buscar notificações por prioridade"""
        return db.query(Notification).filter(Notification.priority == priority).all()

    def get_unread(self, db: Session) -> List[Notification]:
        """Buscar notificações não lidas"""
        return db.query(Notification).filter(Notification.read_status is False).all()

    def get_action_required(self, db: Session) -> List[Notification]:
        """Buscar notificações que requerem ação"""
        return db.query(Notification).filter(Notification.action_required is True).all()

    def get_by_related(self, db: Session, related_type: str, related_id: str) -> List[Notification]:
        """Buscar notificações por entidade relacionada"""
        return (
            db.query(Notification)
            .filter(
                Notification.related_type == related_type, Notification.related_id == related_id
            )
            .all()
        )

    def mark_as_read(self, db: Session, notification_id: str) -> Optional[Notification]:
        """Marcar notificação como lida"""
        notification_obj = self.get(db, notification_id)
        if notification_obj:
            notification_obj.read_status = True
            db.commit()
            db.refresh(notification_obj)
            return notification_obj
        return None

    def mark_all_as_read(self, db: Session) -> int:
        """Marcar todas as notificações como lidas"""
        count = db.query(Notification).filter(Notification.read_status is False).count()
        db.query(Notification).filter(Notification.read_status is False).update(
            {"read_status": True}
        )
        db.commit()
        return count

    def delete_old_notifications(self, db: Session, days_old: int = 30) -> int:
        """Deletar notificações antigas"""
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        count = (
            db.query(Notification)
            .filter(Notification.created_at < cutoff_date, Notification.read_status is True)
            .count()
        )

        db.query(Notification).filter(
            Notification.created_at < cutoff_date, Notification.read_status is True
        ).delete()

        db.commit()
        return count

    def get_recent(self, db: Session, limit: int = 10) -> List[Notification]:
        """Buscar notificações mais recentes"""
        return db.query(Notification).order_by(Notification.created_at.desc()).limit(limit).all()
