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

    # ── 3. Contratos vincendos em até 90 dias ──
    contratos_vincendos = (
        db.query(Contract)
        .filter(
            Contract.user_id == user_id,
            Contract.status == "ativo",
            Contract.end_date >= today,
            Contract.end_date <= today + timedelta(days=90),
        )
        .all()
    )
    expiring_soon = len(contratos_vincendos)

    # ── 4. Gerar notificações ──
    # O endpoint POST /notifications/process-background-tasks/ documentava a
    # geração de notificações de inadimplência, vencimento e lembretes, mas
    # nenhuma linha aqui as criava: `has_recent_notification` (a lógica
    # antispam citada na docstring) nunca era chamada. A funcionalidade
    # existia só no texto.
    notificacoes_criadas = _gerar_notificacoes(db, user_id, today, contratos_vincendos)

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
        "notifications_created": notificacoes_criadas,
    }


def _gerar_notificacoes(
    db: Session,
    user_id: int,
    today: date,
    contratos_vincendos: List[Contract],
) -> int:
    """
    Cria as notificações que o endpoint sempre prometeu.

    Antispam: `has_recent_notification` impede repetir o mesmo alerta para a
    mesma entidade dentro de 7 dias. Sem isso, o job diário geraria uma
    notificação por dia para cada pagamento atrasado até ele ser quitado, e o
    usuário aprenderia a ignorar o sino.
    """
    from src.notifications.repository import NotificationRepository
    from src.notifications.schema import NotificationCreateInternal

    repo = NotificationRepository(db)
    criadas = 0

    def _criar(**dados) -> None:
        nonlocal criadas
        repo.create(NotificationCreateInternal(user_id=user_id, **dados))
        criadas += 1

    # ── Pagamentos atrasados ──
    atrasados = (
        db.query(Payment)
        .filter(Payment.user_id == user_id, Payment.status == "atrasado")
        .all()
    )
    for pagamento in atrasados:
        if repo.has_recent_notification(user_id, str(pagamento.id), "payment_overdue"):
            continue
        dias = (today - pagamento.due_date).days
        _criar(
            type="payment_overdue",
            title="Pagamento em atraso",
            message=(
                f"Pagamento de R$ {pagamento.total_amount} venceu há {dias} dia(s) "
                f"(vencimento em {pagamento.due_date:%d/%m/%Y})."
            ),
            priority="urgent" if dias > 30 else "high",
            action_required=True,
            related_id=str(pagamento.id),
            related_type="payment",
            date=today,
        )

    # ── Contratos próximos do vencimento ──
    for contrato in contratos_vincendos:
        if repo.has_recent_notification(user_id, str(contrato.id), "contract_expiring"):
            continue
        dias = (contrato.end_date - today).days
        _criar(
            type="contract_expiring",
            title="Contrato próximo do vencimento",
            message=(
                f"O contrato \"{contrato.title}\" vence em {dias} dia(s) "
                f"({contrato.end_date:%d/%m/%Y})."
            ),
            priority="high" if dias <= 30 else "medium",
            action_required=dias <= 30,
            related_id=str(contrato.id),
            related_type="contract",
            date=today,
        )

    # ── Lembretes de pagamento (vencendo nos próximos 3 dias) ──
    a_vencer = (
        db.query(Payment)
        .filter(
            Payment.user_id == user_id,
            Payment.status == "pendente",
            Payment.due_date >= today,
            Payment.due_date <= today + timedelta(days=3),
        )
        .all()
    )
    for pagamento in a_vencer:
        if repo.has_recent_notification(user_id, str(pagamento.id), "reminder"):
            continue
        _criar(
            type="reminder",
            title="Pagamento a vencer",
            message=(
                f"Pagamento de R$ {pagamento.total_amount} vence em "
                f"{pagamento.due_date:%d/%m/%Y}."
            ),
            priority="medium",
            related_id=str(pagamento.id),
            related_type="payment",
            date=today,
        )

    return criadas


# ────────────────────────────────────────────────────────────────
# APScheduler — tarefa diária automática
# ────────────────────────────────────────────────────────────────

_scheduler = None  # singleton


# Identificador arbitrário mas fixo do advisory lock. Precisa ser o mesmo em
# todas as instâncias para que disputem o mesmo lock.
_LOCK_DAILY_CHECK = 20260812


def _daily_check():
    """
    Executado pelo scheduler. Roda `run_background_checks` para
    **todos** os user_ids que possuem propriedades cadastradas.

    O scheduler sobe dentro do processo da aplicação, então com múltiplos
    workers (`--workers N`) ou réplicas, esta função dispararia N vezes em
    paralelo sobre as mesmas linhas — disputando o UPDATE de status e
    multiplicando o trabalho. O advisory lock garante que apenas uma instância
    execute; as demais desistem imediatamente.
    """
    from sqlalchemy import text

    from src.database import SessionLocal

    db: Session = SessionLocal()
    # Inicializado antes do try: o `finally` o consulta, e a própria aquisição
    # do lock pode falhar.
    obteve_lock = False
    try:
        obteve_lock = bool(
            db.execute(
                text("SELECT pg_try_advisory_lock(:chave)"),
                {"chave": _LOCK_DAILY_CHECK},
            ).scalar()
        )

        if not obteve_lock:
            logger.info("daily_check já em execução em outra instância — ignorando.")
            return

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
        # Libera o lock explicitamente. Ele cairia junto com a conexão, mas
        # com NullPool + PgBouncer a conexão pode ser reaproveitada, e um lock
        # esquecido bloquearia a execução do dia seguinte.
        try:
            if obteve_lock:
                db.execute(
                    text("SELECT pg_advisory_unlock(:chave)"),
                    {"chave": _LOCK_DAILY_CHECK},
                )
                db.commit()
        except Exception:
            logger.exception("Falha ao liberar o advisory lock do daily_check")
        db.close()


def start_scheduler():
    """Iniciar o APScheduler com CronTrigger diário às 06:00 BRT."""
    global _scheduler

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning("APScheduler não instalado — scheduler desativado.")
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
    logger.info("Scheduler iniciado — daily_check às 06:00 BRT")


def shutdown_scheduler():
    """Encerrar o scheduler de forma limpa."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler encerrado")
