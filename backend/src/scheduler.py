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
from src.payments.models import Payment
from src.properties.models import Property
from src.tenants.models import Tenant

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

    # ── 1. Atualizar pagamentos pendentes/parciais vencidos → 'atrasado' ──
    pending_to_overdue = (
        db.query(Payment)
        .filter(
            Payment.user_id == user_id,
            Payment.status.in_(["pendente", "parcial"]),
            Payment.due_date < today,
        )
        .update({"status": "atrasado"}, synchronize_session=False)
    )
    db.commit()

    total_overdue = db.query(Payment).filter(Payment.user_id == user_id, Payment.status == "atrasado").count()
    total_pending = db.query(Payment).filter(Payment.user_id == user_id, Payment.status == "pendente").count()
    total_paid = db.query(Payment).filter(Payment.user_id == user_id, Payment.status == "pago").count()
    total_partial = db.query(Payment).filter(Payment.user_id == user_id, Payment.status == "parcial").count()

    # ── 2. Auto-expirar contratos vencidos e liberar imóvel ──
    expired_contracts = (
        db.query(Contract)
        .filter(
            Contract.user_id == user_id,
            Contract.status == "ativo",
            Contract.end_date < today,
        )
        .all()
    )
    auto_expired = 0
    for contract in expired_contracts:
        contract.status = "expirado"
        # Liberar o imóvel associado
        prop = db.query(Property).filter(Property.id == contract.property_id).first()
        if prop:
            prop.status = "vacant"
            prop.tenant_id = None
        auto_expired += 1
    db.commit()

    # ── 3. Contratos vincendos em 30, 60 e 90 dias (apenas contagem) ──
    expiring_soon = (
        db.query(Contract)
        .filter(
            Contract.user_id == user_id,
            Contract.status == "ativo",
            Contract.end_date >= today,
            Contract.end_date <= today + timedelta(days=90),
        )
        .count()
    )

    return {
        "payment_status_changes": {
            "pending_to_overdue": pending_to_overdue,
            "total_overdue": total_overdue,
            "total_pending": total_pending,
            "total_paid": total_paid,
            "total_partial": total_partial,
        },
        "contracts_auto_expired": auto_expired,
        "expiring_soon": expiring_soon,
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
                    "  user_id=%d  overdue=%d  expired=%d  expiring=%d",
                    uid,
                    result["payment_status_changes"]["pending_to_overdue"],
                    result["contracts_auto_expired"],
                    result["expiring_soon"],
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
        name="Verificação diária de contratos e pagamentos",
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
