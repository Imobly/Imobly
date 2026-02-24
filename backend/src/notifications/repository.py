"""
Repository para o módulo de notificações
"""

from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from .models import Notification
from .schema import NotificationCreateInternal, NotificationUpdate


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        read: Optional[bool] = None,
        type: Optional[str] = None,
    ) -> List[Notification]:
        q = self.db.query(Notification).filter(Notification.user_id == user_id)
        if read is not None:
            q = q.filter(Notification.read_status == read)
        if type:
            q = q.filter(Notification.type == type)
        return q.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_id_and_user(self, notification_id: int, user_id: int) -> Optional[Notification]:
        return (
            self.db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )

    def get_unread(self, user_id: int) -> List[Notification]:
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.read_status == False)
            .order_by(Notification.created_at.desc())
            .all()
        )

    def count_unread(self, user_id: int) -> int:
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.read_status == False)
            .count()
        )

    def create(self, data: NotificationCreateInternal) -> Notification:
        obj = Notification(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(
        self, notification_id: int, user_id: int, data: NotificationUpdate
    ) -> Optional[Notification]:
        obj = self.get_by_id_and_user(notification_id, user_id)
        if not obj:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def mark_as_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
        obj = self.get_by_id_and_user(notification_id, user_id)
        if not obj:
            return None
        obj.read_status = True
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def mark_all_as_read(self, user_id: int) -> int:
        result = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.read_status == False)
            .update({"read_status": True}, synchronize_session=False)
        )
        self.db.commit()
        return result

    def delete(self, notification_id: int, user_id: int) -> bool:
        obj = self.get_by_id_and_user(notification_id, user_id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True

    def delete_old(self, user_id: int, days: int = 30) -> int:
        cutoff = date.today() - timedelta(days=days)
        result = (
            self.db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.read_status == True,
                Notification.date < cutoff,
            )
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return result
