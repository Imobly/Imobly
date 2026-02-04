from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .repository import NotificationRepository
from .schemas import Notification, NotificationCreate, NotificationUpdate


class notification_controller:
    """Controller para gerenciar operações de notificações"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = NotificationRepository(db)

    def get_notifications(self, db: Session, skip: int = 0, limit: int = 100) -> List[Notification]:
        """Listar notificações"""
        return self.repository.get_multi(db, skip=skip, limit=limit)

    def get_notification_by_id(self, db: Session, notification_id: int) -> Notification:
        """Obter notificação por ID"""
        notification_obj = self.repository.get(db, notification_id)
        if not notification_obj:
            raise HTTPException(status_code=404, detail="Notificação não encontrada")
        return notification_obj

    def create_notification(
        self, db: Session, notification_data: NotificationCreate
    ) -> Notification:
        """Criar nova notificação"""
        return self.repository.create(db, obj_in=notification_data)

    def update_notification(
        self, db: Session, notification_id: int, notification_data: NotificationUpdate
    ) -> Notification:
        """Atualizar notificação existente"""
        notification_obj = self.repository.get(db, notification_id)
        if not notification_obj:
            raise HTTPException(status_code=404, detail="Notificação não encontrada")

        return self.repository.update(db, db_obj=notification_obj, obj_in=notification_data)

    def delete_notification(self, db: Session, notification_id: int) -> dict:
        """Deletar notificação"""
        success = self.repository.delete(db, id=notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notificação não encontrada")
        return {"message": "Notificação deletada com sucesso"}

    def mark_as_read(self, db: Session, notification_id: int) -> Notification:
        """Marcar notificação como lida"""
        notification_obj = self.repository.mark_as_read(db, notification_id)
        if not notification_obj:
            raise HTTPException(status_code=404, detail="Notificação não encontrada")
        return notification_obj


# Instância global do controller
