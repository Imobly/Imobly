"""
Background tasks para processar notificações e status automaticamente
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.notification_service import NotificationService
from app.core.payment_service import PaymentCalculationService
from app.src.contracts.models import Contract
from app.src.payments.models import Payment


class BackgroundTasksService:
    """Serviço para executar tarefas em background"""

    @staticmethod
    def process_contract_expiring_notifications(db: Session, user_id: int) -> int:
        """
        Processa notificações de contratos vencendo

        Args:
            db: Sessão do banco
            user_id: ID do usuário

        Returns:
            Número de notificações criadas
        """
        # Buscar contratos ativos do usuário
        contracts = (
            db.query(Contract)
            .filter(Contract.user_id == user_id, Contract.status == "active")
            .all()
        )

        notifications_created = 0

        for contract in contracts:
            notification_type = (
                PaymentCalculationService.should_send_contract_expiring_notification(contract)
            )

            if notification_type:
                days = 60 if notification_type == "60_days" else 30

                # Verificar se já não existe notificação similar recente
                from datetime import timedelta

                from app.src.notifications.models import Notification

                recent_notification = (
                    db.query(Notification)
                    .filter(
                        Notification.user_id == user_id,
                        Notification.type == "contract_expiring",
                        Notification.related_id == str(contract.id),
                        Notification.created_at
                        >= datetime.utcnow() - timedelta(days=3),  # Últimos 3 dias
                    )
                    .first()
                )

                if not recent_notification:
                    NotificationService.create_contract_expiring_notification(
                        db=db, contract=contract, days_until_expiry=days
                    )
                    notifications_created += 1

        return notifications_created

    @staticmethod
    def process_payment_reminders(db: Session, user_id: int) -> int:
        """
        Processa lembretes de pagamentos próximos do vencimento

        Args:
            db: Sessão do banco
            user_id: ID do usuário

        Returns:
            Número de notificações criadas
        """
        # Buscar pagamentos pendentes ou atrasados
        payments = (
            db.query(Payment)
            .filter(Payment.user_id == user_id, Payment.status.in_(["pending", "overdue"]))
            .all()
        )

        notifications_created = 0
        current_date = datetime.now().date()

        for payment in payments:
            days_until_due = (payment.due_date - current_date).days

            # Verificar se deve enviar lembrete
            due_date_val = (
                payment.due_date if isinstance(payment.due_date, date) else payment.due_date
            )
            reminder_type = PaymentCalculationService.should_send_payment_reminder(due_date_val)  # type: ignore[arg-type]

            if reminder_type:
                # Verificar se já não existe notificação similar recente
                from datetime import timedelta

                from app.src.notifications.models import Notification

                recent_notification = (
                    db.query(Notification)
                    .filter(
                        Notification.user_id == user_id,
                        Notification.type == "reminder",
                        Notification.related_id == str(payment.id),
                        Notification.created_at >= datetime.utcnow() - timedelta(hours=12),
                    )
                    .first()
                )

                if not recent_notification:
                    NotificationService.create_payment_reminder_notification(
                        db=db, payment=payment, days_until_due=days_until_due
                    )
                    notifications_created += 1

        return notifications_created

    @staticmethod
    def process_overdue_payment_notifications(db: Session, user_id: int) -> int:
        """
        Processa notificações de pagamentos atrasados

        Args:
            db: Sessão do banco
            user_id: ID do usuário

        Returns:
            Número de notificações criadas
        """
        # Buscar pagamentos atrasados
        payments = (
            db.query(Payment).filter(Payment.user_id == user_id, Payment.status == "overdue").all()
        )

        notifications_created = 0

        for payment in payments:
            due_date_val = (
                payment.due_date if isinstance(payment.due_date, date) else payment.due_date
            )
            days_overdue = PaymentCalculationService.calculate_days_overdue(due_date_val)  # type: ignore[arg-type]

            if days_overdue > 0:
                # Enviar notificação a cada 7 dias de atraso
                if days_overdue % 7 == 0 or days_overdue == 1:
                    # Verificar se já não existe notificação similar recente
                    from datetime import timedelta

                    from app.src.notifications.models import Notification

                    recent_notification = (
                        db.query(Notification)
                        .filter(
                            Notification.user_id == user_id,
                            Notification.type == "payment_overdue",
                            Notification.related_id == str(payment.id),
                            Notification.created_at >= datetime.utcnow() - timedelta(days=3),
                        )
                        .first()
                    )

                    if not recent_notification:
                        # Recalcular valores com multa e juros
                        from app.src.contracts.models import Contract

                        contract = (
                            db.query(Contract).filter(Contract.id == payment.contract_id).first()
                        )

                        if contract:
                            (
                                _,
                                _,
                                total_addition,
                            ) = PaymentCalculationService.calculate_fine_and_interest(
                                Decimal(str(payment.amount)),
                                Decimal(str(contract.fine_rate)),
                                Decimal(str(contract.interest_rate)),
                                days_overdue,
                            )
                            total_amount = Decimal(str(payment.amount)) + total_addition

                            NotificationService.create_payment_overdue_notification(
                                db=db,
                                payment=payment,
                                days_overdue=days_overdue,
                                total_amount=Decimal(str(total_amount)),
                            )
                            notifications_created += 1

        return notifications_created

    @staticmethod
    def update_payment_statuses_automatically(db: Session, user_id: int) -> dict:
        """
        Atualiza automaticamente os status de todos os pagamentos

        Args:
            db: Sessão do banco
            user_id: ID do usuário

        Returns:
            Dict com contadores de mudanças
        """
        # Buscar todos os pagamentos do usuário
        payments = db.query(Payment).filter(Payment.user_id == user_id).all()

        changes = {
            "pending_to_overdue": 0,
            "total_overdue": 0,
            "total_pending": 0,
            "total_paid": 0,
            "total_partial": 0,
        }

        for payment in payments:
            old_status = payment.status

            # Converter Column para tipos Python
            due_date_val = (
                payment.due_date if isinstance(payment.due_date, date) else payment.due_date
            )
            payment_date_val = (
                payment.payment_date
                if payment.payment_date is None or isinstance(payment.payment_date, date)
                else payment.payment_date
            )
            amount_val = Decimal(str(payment.amount)) if payment.payment_date else None
            total_val = Decimal(str(payment.total_amount))

            # Determinar novo status
            new_status = PaymentCalculationService.determine_payment_status(
                due_date_val,  # type: ignore[arg-type]
                payment_date_val,  # type: ignore[arg-type]
                amount_val,
                total_val,
            )

            # Atualizar se mudou
            if old_status != new_status:
                setattr(payment, "status", new_status)

                if old_status == "pending" and new_status == "overdue":
                    changes["pending_to_overdue"] += 1

            # Contabilizar
            key = f"total_{new_status}"
            changes[key] = changes.get(key, 0) + 1

        db.commit()

        return changes

    @classmethod
    def run_all_background_tasks(cls, db: Session, user_id: int) -> dict:
        """
        Executa todas as tarefas de background

        Args:
            db: Sessão do banco
            user_id: ID do usuário

        Returns:
            Dict com resultados de todas as tarefas
        """
        results: dict = {}

        # Atualizar status de pagamentos
        results["payment_status_changes"] = cls.update_payment_statuses_automatically(db, user_id)

        # Processar notificações de contratos vencendo
        results["contract_notifications"] = cls.process_contract_expiring_notifications(db, user_id)

        # Processar lembretes de pagamento
        results["payment_reminders"] = cls.process_payment_reminders(db, user_id)

        # Processar notificações de atraso
        results["overdue_notifications"] = cls.process_overdue_payment_notifications(db, user_id)

        return results
