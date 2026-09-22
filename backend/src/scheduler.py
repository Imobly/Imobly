"""
Motor de inteligência — Scheduler diário + lógica de verificação reutilizável.

• APScheduler (BackgroundScheduler) executa `daily_check` todos os dias às 06:00 BRT.
• `run_background_checks(db, user_id)` contém a lógica compartilhada entre o
  scheduler automático e o endpoint manual POST /process-background-tasks/.

O que o job faz, em ordem:

  1. emite as cobranças do mês (idempotente — este passo não existia, e sem ele
     a parcela de cada contrato teria que ser digitada à mão todo mês);
  2. reconcilia o status das cobranças em aberto;
  3. expira contratos vencidos e libera o imóvel;
  4. gera notificações.

Sobre as notificações — a regra é NOTIFICAR MUDANÇA DE ESTADO, NUNCA ESTADO.
"Fulano ficou inadimplente hoje" é notificação. "Fulano está inadimplente há 40
dias" é painel: número que se consulta, filtra e ordena, coisa que uma lista de
avisos faz mal. A versão anterior emitia um alerta por cobrança atrasada a cada
7 dias; numa carteira com 60 inadimplentes isso são 60 cartões se repetindo até
o fim da dívida, e o usuário aprende a ignorar o sino.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from src.charges.calculo import situacao_inquilino
from src.charges.geracao import gerar_cobrancas
from src.charges.models import Charge
from src.charges.repository import ChargeRepository
from src.contracts.models import Contract
from src.properties.models import Property

logger = logging.getLogger("imobly.scheduler")

BRT = ZoneInfo("America/Sao_Paulo")

# Escalonamento da cobrança. Cada limiar dispara UMA vez por cobrança: o
# primeiro é o aviso, o de 15 dias é a cobrança formal, o de 30 é a decisão
# sobre medida judicial. Notificar todo dia não acrescenta informação nenhuma
# depois do primeiro aviso — só treina o usuário a não olhar.
LIMIARES_ATRASO = (1, 15, 30)

# A partir de quantos dias o inquilino deixa de ser "atraso leve".
DIAS_PARA_INADIMPLENCIA = 15


def _today_brt() -> date:
    return datetime.now(BRT).date()


def run_background_checks(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Executa todas as verificações de inteligência para um único usuário.

    Retorna um dict com contadores para log / resposta da API.
    """
    today = _today_brt()
    repo = ChargeRepository(db)

    # ── 1. Emitir as cobranças da competência corrente ──
    geracao = gerar_cobrancas(db, user_id, competencia=today)

    # ── 2. Reconciliar o status das cobranças em aberto ──
    # `aberta` → `vencida` é a única transição que o tempo provoca sozinho. O
    # UPDATE em massa antigo também reescrevia `parcial` como `atrasado`,
    # apagando a informação de que houve pagamento — exatamente o dado mais
    # importante para decidir como cobrar.
    status_alterados = repo.sincronizar_status_em_lote(user_id, hoje=today)

    contagens = {
        chave: db.query(Charge)
        .filter(Charge.user_id == user_id, Charge.status == chave)
        .count()
        for chave in ("aberta", "parcial", "vencida", "quitada")
    }

    # ── 3. Auto-expirar contratos vencidos e liberar imóvel ──
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
        prop = db.query(Property).filter(Property.id == contract.property_id).first()
        if prop:
            prop.status = "vacant"
            prop.tenant_id = None
        auto_expired += 1
    db.commit()

    # ── 4. Contratos vincendos em até 90 dias ──
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

    # ── 5. Notificações ──
    notificacoes_criadas = _gerar_notificacoes(db, repo, user_id, today, contratos_vincendos)

    return {
        "charges_generated": geracao["created"],
        "charges_already_existing": geracao["skipped_existing"],
        "charges_without_due_day": geracao["skipped_no_due_day"],
        "payment_status_changes": {
            "status_reconciled": status_alterados,
            "total_open": contagens["aberta"],
            "total_partial": contagens["parcial"],
            "total_overdue": contagens["vencida"],
            "total_settled": contagens["quitada"],
            # Chaves antigas mantidas: o frontend e os testes as consomem.
            "pending_to_overdue": status_alterados,
            "total_pending": contagens["aberta"],
            "total_paid": contagens["quitada"],
        },
        "contracts_auto_expired": auto_expired,
        "expiring_soon": expiring_soon,
        "notifications_created": notificacoes_criadas,
    }


def _moeda(valor: Decimal) -> str:
    """Formata em pt-BR: 1.234,56 — o padrão que o usuário lê no extrato."""
    return f"{valor:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _gerar_notificacoes(
    db: Session,
    repo: ChargeRepository,
    user_id: int,
    today: date,
    contratos_vincendos: List[Contract],
) -> int:
    """
    Cria as notificações de mudança de estado.

    São quatro, e nenhuma delas repete um aviso já dado:

      • atraso cruzou um limiar (1/15/30 dias) — uma vez por cobrança e limiar;
      • inquilino entrou em inadimplência (>15 dias) — uma vez por inquilino;
      • contrato entrando na janela de renovação;
      • lembrete AGRUPADO do que vence nos próximos 3 dias — uma notificação
        por dia, não uma por cobrança.
    """
    from src.notifications.models import Notification
    from src.notifications.repository import NotificationRepository
    from src.notifications.schema import NotificationCreateInternal

    notif_repo = NotificationRepository(db)
    criadas = 0

    def _criar(**dados) -> None:
        nonlocal criadas
        notif_repo.create(NotificationCreateInternal(user_id=user_id, **dados))
        criadas += 1

    # Limiares já avisados, numa query só. Sem isto o job diário repetiria o
    # mesmo alerta indefinidamente — o defeito que o antispam por janela de 7
    # dias apenas atenuava, sem resolver.
    ja_avisados = {
        (n.related_id, (n.notification_metadata or {}).get("threshold"))
        for n in db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.type == "payment_overdue")
        .all()
    }

    charges = repo.cobrancas_em_aberto(user_id)
    posicoes = repo.posicoes(charges, hoje=today)
    tenants, properties = repo.nomes_relacionados(charges, user_id)

    # ── Atraso cruzando limiar ──
    por_inquilino: Dict[int, Dict[str, Any]] = {}
    for charge in charges:
        posicao = posicoes[charge.id]
        if posicao.saldo <= 0:
            continue

        acumulado = por_inquilino.setdefault(
            charge.tenant_id, {"saldo": Decimal("0.00"), "dias": 0}
        )
        acumulado["saldo"] += posicao.saldo
        acumulado["dias"] = max(acumulado["dias"], posicao.dias_atraso)

        if posicao.dias_atraso <= 0:
            continue

        # O maior limiar já cruzado — e não "o limiar de hoje". Se o job ficar
        # um dia fora do ar, o aviso de 15 dias ainda sai no dia 16 em vez de
        # ser pulado para sempre.
        limiar = max((l for l in LIMIARES_ATRASO if posicao.dias_atraso >= l), default=None)
        if limiar is None or (str(charge.id), limiar) in ja_avisados:
            continue

        inquilino = tenants.get(charge.tenant_id, "Inquilino")
        imovel = properties.get(charge.property_id, "imóvel")
        parcial = posicao.pago > 0

        _criar(
            type="payment_overdue",
            title=(
                f"{inquilino} — {posicao.dias_atraso} dias de atraso"
                if limiar > 1
                else f"{inquilino} — cobrança vencida"
            ),
            message=(
                f"{imovel}: saldo de R$ {_moeda(posicao.saldo)} em aberto "
                f"(venceu em {charge.due_date:%d/%m/%Y})."
                + (
                    f" Pagamento parcial de R$ {_moeda(posicao.pago)} já registrado."
                    if parcial
                    else ""
                )
            ),
            priority="urgent" if limiar >= 30 else "high",
            action_required=True,
            related_id=str(charge.id),
            related_type="payment",
            link=f"/payments?charge={charge.id}",
            date=today,
            metadata={
                "threshold": limiar,
                "charge_id": charge.id,
                "tenant_id": charge.tenant_id,
                "property_id": charge.property_id,
                "balance": str(posicao.saldo),
                "days_overdue": posicao.dias_atraso,
                "partial": parcial,
            },
        )

    # ── Inquilino entrou em inadimplência ──
    for tenant_id, dados in por_inquilino.items():
        if situacao_inquilino(dados["dias"], dados["saldo"]) not in ("inadimplente", "critico"):
            continue
        if notif_repo.has_recent_notification(
            user_id, f"tenant:{tenant_id}", "tenant_delinquent", days=30
        ):
            continue
        _criar(
            type="tenant_delinquent",
            title=f"{tenants.get(tenant_id, 'Inquilino')} está inadimplente",
            message=(
                f"Dívida total de R$ {_moeda(dados['saldo'])}, "
                f"atraso mais antigo de {dados['dias']} dias."
            ),
            priority="urgent" if dados["dias"] > 60 else "high",
            action_required=True,
            related_id=f"tenant:{tenant_id}",
            related_type="payment",
            link=f"/tenants?tenant={tenant_id}",
            date=today,
            metadata={"tenant_id": tenant_id, "balance": str(dados["saldo"])},
        )

    # ── Contratos próximos do vencimento ──
    for contrato in contratos_vincendos:
        if notif_repo.has_recent_notification(user_id, str(contrato.id), "contract_expiring", days=30):
            continue
        dias = (contrato.end_date - today).days
        _criar(
            type="contract_expiring",
            title="Contrato próximo do vencimento",
            message=(
                f'O contrato "{contrato.title}" vence em {dias} dia(s) '
                f"({contrato.end_date:%d/%m/%Y})."
            ),
            priority="high" if dias <= 30 else "medium",
            action_required=dias <= 30,
            related_id=str(contrato.id),
            related_type="contract",
            link=f"/properties?contract={contrato.id}",
            date=today,
        )

    # ── Lembrete AGRUPADO do que vence em até 3 dias ──
    # Uma notificação com o total e o link para a lista filtrada vale mais que
    # doze cartões idênticos que o usuário fecha sem ler.
    a_vencer = [
        (c, posicoes[c.id])
        for c in charges
        if posicoes[c.id].saldo > 0
        and today <= c.due_date <= today + timedelta(days=3)
    ]
    if a_vencer and not notif_repo.has_recent_notification(
        user_id, f"vencimentos:{today.isoformat()}", "reminder", days=1
    ):
        total = sum((p.saldo for _, p in a_vencer), Decimal("0.00"))
        _criar(
            type="reminder",
            title=f"{len(a_vencer)} cobrança(s) vencem nos próximos 3 dias",
            message=f"Total de R$ {_moeda(total)} a receber até {today + timedelta(days=3):%d/%m/%Y}.",
            priority="medium",
            related_id=f"vencimentos:{today.isoformat()}",
            related_type="payment",
            link="/payments?filter=a_vencer",
            date=today,
            metadata={"count": len(a_vencer), "total": str(total)},
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
    multiplicando o trabalho. Com a geração de cobranças no caminho, o dano
    passou de desperdício a duplicidade de cobrança para o inquilino (a UNIQUE
    de `charges` barra, mas a transação inteira falharia). O advisory lock
    garante que apenas uma instância execute; as demais desistem imediatamente.
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

        user_ids = [uid for (uid,) in db.query(Property.user_id).distinct().all()]
        logger.info("⏰ Scheduler daily_check — %d usuários", len(user_ids))
        for uid in user_ids:
            try:
                result = run_background_checks(db, uid)
                logger.info(
                    "  user_id=%d  emitidas=%d  vencidas=%d  expirados=%d  notificações=%d",
                    uid,
                    result["charges_generated"],
                    result["payment_status_changes"]["total_overdue"],
                    result["contracts_auto_expired"],
                    result["notifications_created"],
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
