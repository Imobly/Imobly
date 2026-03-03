"""
Motor de inteligência — Scheduler diário + lógica de verificação reutilizável.

• APScheduler (BackgroundScheduler) executa `daily_check` todos os dias às 06:00 BRT.
• `run_background_checks(db, user_id)` contém a lógica compartilhada entre o
  scheduler automático e o endpoint manual POST /process-background-tasks/.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from src.contracts.models import Contract
from src.notifications.models import Notification
from src.notifications.repository import NotificationRepository
from src.notifications.schema import NotificationCreateInternal
from src.payments.models import Payment
from src.properties.models import Property

logger = logging.getLogger("imobly.scheduler")

BRT = ZoneInfo("America/Sao_Paulo")

# ────────────────────────────────────────────────────────────────
# Lógica reutilizável (scheduler + endpoint manual)
# ────────────────────────────────────────────────────────────────


def _today_brt() -> date:
    return datetime.now(BRT).date()


def run_background_checks(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Executa todas as verificações de inteligência para um único usuário.

    Retorna um dict com contadores para log / resposta da API.
    """
    today = _today_brt()
    repo = NotificationRepository(db)

    # ── 1. Atualizar pagamentos pendentes vencidos → 'overdue' ──
    pending_to_overdue = (
        db.query(Payment)
        .filter(
            Payment.user_id == user_id,
            Payment.status.in_(["pending", "partial"]),
            Payment.due_date < today,
        )
        .update({"status": "overdue"}, synchronize_session=False)
    )
    db.commit()

    total_overdue = db.query(Payment).filter(Payment.user_id == user_id, Payment.status == "overdue").count()
    total_pending = db.query(Payment).filter(Payment.user_id == user_id, Payment.status == "pending").count()
    total_paid = db.query(Payment).filter(Payment.user_id == user_id, Payment.status == "paid").count()
    total_partial = db.query(Payment).filter(Payment.user_id == user_id, Payment.status == "partial").count()

    # ── 2. Notificações de inadimplência (pagamentos agora overdue) ──
    overdue_payments = (
        db.query(Payment)
        .filter(Payment.user_id == user_id, Payment.status == "overdue")
        .all()
    )
    overdue_notifications = 0
    for p in overdue_payments:
        if repo.has_recent_notification(user_id, str(p.id), "payment_overdue", days=7):
            continue
        repo.create(NotificationCreateInternal(
            user_id=user_id,
            type="payment_overdue",
            title="Pagamento em atraso",
            message=f"O pagamento #{p.id} venceu em {p.due_date}.",
            date=today,
            priority="urgent",
            read_status=False,
            action_required=True,
            related_id=str(p.id),
            related_type="payment",
            metadata={"property_id": p.property_id, "tenant_id": p.tenant_id},
        ))
        overdue_notifications += 1

    # ── 3. Contratos vincendos em 30, 60 e 90 dias ──
    contract_notifications = 0
    for window_days in (30, 60, 90):
        target_date = today + timedelta(days=window_days)
        # Pega contratos cuja end_date esteja na faixa [target - 1, target + 1]
        # para cobrir variantes de fuso e evitar perda de dia
        expiring_contracts: List[Contract] = (
            db.query(Contract)
            .filter(
                Contract.user_id == user_id,
                Contract.status == "active",
                Contract.end_date >= today,
                Contract.end_date <= target_date,
                Contract.end_date > target_date - timedelta(days=window_days - (window_days - 1)),
                # Simplificação: end_date entre hoje e target_date
            )
            .all()
        )
        for c in expiring_contracts:
            if repo.has_recent_notification(user_id, str(c.id), "contract_expiring", days=7):
                continue
            days_left = (c.end_date - today).days
            priority = "urgent" if days_left <= 7 else ("high" if days_left <= 30 else "medium")
            repo.create(NotificationCreateInternal(
                user_id=user_id,
                type="contract_expiring",
                title=f"Contrato vence em {days_left} dias",
                message=f"O contrato #{c.id} vence em {c.end_date}.",
                date=today,
                priority=priority,
                read_status=False,
                action_required=True,
                related_id=str(c.id),
                related_type="contract",
                metadata={"property_id": c.property_id, "tenant_id": c.tenant_id},
            ))
            contract_notifications += 1

    # ── 4. Lembretes de pagamento (próximos 3 dias) ──
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
    for p in upcoming_payments:
        if repo.has_recent_notification(user_id, str(p.id), "reminder", days=7):
            continue
        days_left = (p.due_date - today).days
        repo.create(NotificationCreateInternal(
            user_id=user_id,
            type="reminder",
            title=f"Pagamento vence em {days_left} dia(s)",
            message=f"O pagamento #{p.id} vence em {p.due_date}.",
            date=today,
            priority="high" if days_left == 0 else "medium",
            read_status=False,
            action_required=True,
            related_id=str(p.id),
            related_type="payment",
            metadata={"property_id": p.property_id, "tenant_id": p.tenant_id},
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
        "overdue_notifications": overdue_notifications,
    }


# ────────────────────────────────────────────────────────────────
# APScheduler — tarefa diária automática
# ────────────────────────────────────────────────────────────────

_scheduler = None  # singleton


def _daily_check():
    """
    Executado pelo scheduler.  Roda `run_background_checks` para
    **todos** os user_ids que possuem propriedades cadastradas.
    """
    from src.database import SessionLocal

    db: Session = SessionLocal()
    try:
        user_ids = [
            uid for (uid,) in db.query(Property.user_id).distinct().all()
        ]
        logger.info("⏰ Scheduler daily_check — %d usuários", len(user_ids))
        for uid in user_ids:
            try:
                result = run_background_checks(db, uid)
                logger.info(
                    "  user_id=%d  overdue_notifs=%d  contract_notifs=%d  reminders=%d",
                    uid,
                    result["overdue_notifications"],
                    result["contract_notifications"],
                    result["payment_reminders"],
                )
            except Exception:
                logger.exception("  Erro ao processar user_id=%d", uid)
                db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Iniciar o APScheduler com CronTrigger diário às 06:00 BRT."""
    global _scheduler

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning("⚠️  APScheduler não instalado — scheduler desativado.")
        return

    if _scheduler is not None:
        return  # já rodando

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _daily_check,
        trigger=CronTrigger(hour=6, minute=0, timezone=BRT),
        id="imobly_daily_check",
        name="Verificação diária de contratos, pagamentos e notificações",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("✅ Scheduler iniciado — daily_check às 06:00 BRT")


def shutdown_scheduler():
    """Encerrar o scheduler de forma limpa."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("🛑 Scheduler encerrado")
