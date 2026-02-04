"""
Serviço para gerenciamento de notificações inteligentes
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.src.contracts.models import Contract
from app.src.notifications.models import Notification
from app.src.payments.models import Payment
from app.src.tenants.models import Tenant


class NotificationService:
    """Serviço para criar e gerenciar notificações automaticamente"""

    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        type: str,
        title: str,
        message: str,
        priority: str = "medium",
        action_required: bool = False,
        related_id: Optional[str] = None,
        related_type: Optional[str] = None,
    ) -> Notification:
        """
        Cria uma nova notificação

        Args:
            db: Sessão do banco
            user_id: ID do usuário
            type: Tipo de notificação
            title: Título
            message: Mensagem
            priority: Prioridade (low, medium, high, urgent)
            action_required: Se requer ação
            related_id: ID relacionado
            related_type: Tipo de entidade relacionada

        Returns:
            Notificação criada
        """
        notification = Notification(
            id=str(uuid4()),
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            date=datetime.utcnow(),
            priority=priority,
            read_status=False,
            action_required=action_required,
            related_id=related_id,
            related_type=related_type,
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification

    @classmethod
    def create_contract_expiring_notification(
        cls, db: Session, contract: Contract, days_until_expiry: int
    ) -> Notification:
        """
        Cria notificação de contrato vencendo

        Args:
            db: Sessão do banco
            contract: Contrato vencendo
            days_until_expiry: Dias até vencimento

        Returns:
            Notificação criada
        """
        tenant = db.query(Tenant).filter(Tenant.id == contract.tenant_id).first()
        tenant_name = tenant.name if tenant else "Inquilino desconhecido"

        title = f"Contrato vencendo em {days_until_expiry} dias"
        message = (
            f"O contrato '{contract.title}' do inquilino {tenant_name} "
            f"vence em {days_until_expiry} dias (dia {contract.end_date.strftime('%d/%m/%Y')}). "
            f"É recomendado entrar em contato para renovar ou encerrar o contrato."
        )

        priority = "high" if days_until_expiry <= 30 else "medium"

        return cls.create_notification(
            db=db,
            user_id=int(contract.user_id),
            type="contract_expiring",
            title=title,
            message=message,
            priority=priority,
            action_required=True,
            related_id=str(contract.id),
            related_type="contract",
        )

    @classmethod
    def create_payment_reminder_notification(
        cls, db: Session, payment: Payment, days_until_due: int
    ) -> Notification:
        """
        Cria notificação de lembrete de pagamento

        Args:
            db: Sessão do banco
            payment: Pagamento
            days_until_due: Dias até vencimento

        Returns:
            Notificação criada
        """
        tenant = db.query(Tenant).filter(Tenant.id == payment.tenant_id).first()
        tenant_name = tenant.name if tenant else "Inquilino desconhecido"

        if days_until_due == 0:
            title = f"Pagamento vence HOJE - {tenant_name}"
            message = (
                f"O pagamento do inquilino {tenant_name} vence HOJE "
                f"({payment.due_date.strftime('%d/%m/%Y')}). "
                f"Valor: R$ {payment.amount:.2f}"
            )
            priority = "high"
        else:
            title = f"Pagamento vence em {days_until_due} dias - {tenant_name}"
            message = (
                f"O pagamento do inquilino {tenant_name} vence em {days_until_due} dias "
                f"({payment.due_date.strftime('%d/%m/%Y')}). "
                f"Valor: R$ {payment.amount:.2f}"
            )
            priority = "medium"

        return cls.create_notification(
            db=db,
            user_id=int(payment.user_id),
            type="reminder",
            title=title,
            message=message,
            priority=priority,
            action_required=False,
            related_id=str(payment.id),
            related_type="payment",
        )

    @classmethod
    def create_payment_overdue_notification(
        cls, db: Session, payment: Payment, days_overdue: int, total_amount: Decimal
    ) -> Notification:
        """
        Cria notificação de pagamento atrasado

        Args:
            db: Sessão do banco
            payment: Pagamento atrasado
            days_overdue: Dias de atraso
            total_amount: Valor total com multa e juros

        Returns:
            Notificação criada
        """
        tenant = db.query(Tenant).filter(Tenant.id == payment.tenant_id).first()
        tenant_name = tenant.name if tenant else "Inquilino desconhecido"

        title = f"Pagamento ATRASADO - {tenant_name} ({days_overdue} dias)"
        message = (
            f"O pagamento do inquilino {tenant_name} está atrasado há {days_overdue} dias. "
            f"Data de vencimento: {payment.due_date.strftime('%d/%m/%Y')}. "
            f"Valor original: R$ {payment.amount:.2f}. "
            f"Valor atual com multa/juros: R$ {total_amount:.2f}. "
            f"É necessário entrar em contato com o inquilino."
        )

        # Prioridade aumenta com os dias de atraso
        if days_overdue >= 15:
            priority = "urgent"
        elif days_overdue >= 7:
            priority = "high"
        else:
            priority = "medium"

        return cls.create_notification(
            db=db,
            user_id=int(payment.user_id),
            type="payment_overdue",
            title=title,
            message=message,
            priority=priority,
            action_required=True,
            related_id=str(payment.id),
            related_type="payment",
        )

    @classmethod
    def create_payment_received_notification(cls, db: Session, payment: Payment) -> Notification:
        """
        Cria notificação de pagamento recebido

        Args:
            db: Sessão do banco
            payment: Pagamento recebido

        Returns:
            Notificação criada
        """
        tenant = db.query(Tenant).filter(Tenant.id == payment.tenant_id).first()
        tenant_name = tenant.name if tenant else "Inquilino desconhecido"

        if payment.status == "paid":
            title = f"Pagamento recebido - {tenant_name}"
            message = (
                f"Pagamento do inquilino {tenant_name} foi recebido integralmente. "
                f"Valor: R$ {payment.total_amount:.2f}. "
                f"Data do pagamento: {payment.payment_date.strftime('%d/%m/%Y') if payment.payment_date else 'Não informada'}."
            )
        else:  # partial
            title = f"Pagamento PARCIAL recebido - {tenant_name}"
            message = (
                f"Pagamento parcial do inquilino {tenant_name} foi recebido. "
                f"Valor pago: R$ {payment.amount:.2f}. "
                f"Valor total esperado: R$ {payment.total_amount:.2f}. "
                f"Falta receber: R$ {(payment.total_amount - payment.amount):.2f}."
            )

        return cls.create_notification(
            db=db,
            user_id=int(payment.user_id),
            type="system_alert",
            title=title,
            message=message,
            priority="low",
            action_required=False,
            related_id=str(payment.id),
            related_type="payment",
        )

    @staticmethod
    def get_unread_notifications(db: Session, user_id: int, limit: int = 50) -> List[Notification]:
        """
        Busca notificações não lidas do usuário

        Args:
            db: Sessão do banco
            user_id: ID do usuário
            limit: Limite de resultados

        Returns:
            Lista de notificações não lidas
        """
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.read_status.is_(False))
            .order_by(Notification.date.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_notifications_by_type(
        db: Session, user_id: int, type: str, limit: int = 50
    ) -> List[Notification]:
        """
        Busca notificações por tipo

        Args:
            db: Sessão do banco
            user_id: ID do usuário
            type: Tipo de notificação
            limit: Limite de resultados

        Returns:
            Lista de notificações
        """
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.type == type)
            .order_by(Notification.date.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def mark_as_read(db: Session, notification_id: str, user_id: int) -> Optional[Notification]:
        """
        Marca notificação como lida

        Args:
            db: Sessão do banco
            notification_id: ID da notificação
            user_id: ID do usuário (verificação de segurança)

        Returns:
            Notificação atualizada ou None
        """
        notification = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )

        if notification:
            setattr(notification, "read_status", True)
            setattr(notification, "updated_at", datetime.utcnow())
            db.commit()
            db.refresh(notification)

        return notification

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """
        Marca todas as notificações do usuário como lidas

        Args:
            db: Sessão do banco
            user_id: ID do usuário

        Returns:
            Número de notificações atualizadas
        """
        count = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.read_status.is_(False))
            .update({"read_status": True, "updated_at": datetime.utcnow()})
        )

        db.commit()
        return count

    @staticmethod
    def delete_old_notifications(db: Session, user_id: int, days_old: int = 90) -> int:
        """
        Remove notificações antigas

        Args:
            db: Sessão do banco
            user_id: ID do usuário
            days_old: Dias de idade para deletar

        Returns:
            Número de notificações deletadas
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        count = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.created_at < cutoff_date,
                Notification.read_status.is_(True),  # Apenas lidas
            )
            .delete()
        )

        db.commit()
        return count
