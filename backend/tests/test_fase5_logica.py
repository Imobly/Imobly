"""
Testes de regressão da Fase 5 (M-01 a M-08, M-13).

Concentra os defeitos de lógica e de configuração: coisas que não derrubavam o
servidor, mas faziam a aplicação responder errado em silêncio.
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from src.contracts.models import Contract
from src.payments.models import Payment
from src.properties.models import Property
from src.tenants.models import Tenant


@pytest.fixture
def cenario(db_session, make_user):
    user = make_user("fase5@imobly.com.br", "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
    db_session.flush()

    prop = Property(
        user_id=user.id, name="Imóvel", address="Rua V, 5", neighborhood="Centro",
        city="São Paulo", state="SP", zip_code="01000-000", type="apartment",
        area=70, bedrooms=2, bathrooms=1, parking_spaces=1, rent=2000, status="vacant",
    )
    tenant = Tenant(
        user_id=user.id, name="Inquilino", email="f5@imobly.com.br",
        phone="11999999999", cpf_cnpj="12312312312", profession="Analista",
    )
    db_session.add_all([prop, tenant])
    db_session.flush()

    contrato = Contract(
        user_id=user.id, title="Locação", property_id=prop.id, tenant_id=tenant.id,
        start_date=date.today() - timedelta(days=10),
        end_date=date.today() + timedelta(days=20),
        rent=2000, deposit=0, interest_rate=1, fine_rate=2, status="ativo",
    )
    db_session.add(contrato)
    db_session.flush()
    return {"user": user, "prop": prop, "tenant": tenant, "contrato": contrato}


class TestConfiguracaoDeJWT:
    """M-01 — segredo vazio era aceito em dev e o emissor não era validado."""

    def test_segredo_vazio_aborta_o_startup(self, monkeypatch):
        """
        O PyJWT aceita HS256 com chave vazia: com o segredo em branco, qualquer
        pessoa forjaria um token válido. Antes só era exigido fora de dev.
        """
        from src.config import Settings

        cfg = Settings(SUPABASE_JWT_SECRET="", ENVIRONMENT="development")
        with pytest.raises(RuntimeError, match="SUPABASE_JWT_SECRET"):
            cfg.validate_runtime()

    def test_emissor_derivado_da_url_do_supabase(self):
        from src.config import Settings

        cfg = Settings(SUPABASE_URL="https://projeto.supabase.co/")
        assert cfg.jwt_issuer == "https://projeto.supabase.co/auth/v1"

    def test_sem_url_nao_ha_emissor_a_validar(self):
        from src.config import Settings

        assert Settings(SUPABASE_URL="").jwt_issuer is None


class TestControleDeAcessoAdministrativo:
    """M-02 — `require_admin` comparava um papel que nunca era atribuído."""

    def test_usuario_comum_e_barrado(self, db_session, make_user):
        from fastapi import HTTPException
        from src.security import require_admin

        user = make_user("comum@imobly.com.br", "cccccccc-cccc-4ccc-8ccc-cccccccccccc")
        db_session.flush()

        class _Req:
            url = type("U", (), {"path": "/admin"})()

        with pytest.raises(HTTPException) as exc:
            require_admin(
                _Req(),
                {"id": user.supabase_uid, "email": user.email, "payload": {}},
                db_session,
            )
        assert exc.value.status_code == 403

    def test_superusuario_do_banco_e_aceito(self, db_session, make_user):
        from src.security import require_admin

        user = make_user("admin@imobly.com.br", "dddddddd-dddd-4ddd-8ddd-dddddddddddd")
        user.is_superuser = True
        db_session.flush()

        class _Req:
            url = type("U", (), {"path": "/admin"})()

        resultado = require_admin(
            _Req(),
            {"id": user.supabase_uid, "email": user.email, "payload": {}},
            db_session,
        )
        assert resultado["email"] == user.email

    def test_papel_no_app_metadata_do_token_e_aceito(self, db_session, make_user):
        from src.security import require_admin

        user = make_user("meta@imobly.com.br", "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")
        db_session.flush()

        class _Req:
            url = type("U", (), {"path": "/admin"})()

        resultado = require_admin(
            _Req(),
            {
                "id": user.supabase_uid, "email": user.email,
                "payload": {"app_metadata": {"role": "admin"}},
            },
            db_session,
        )
        assert resultado["email"] == user.email


class TestNotificacoesGeradas:
    """M-03 — o endpoint documentava geração de notificações que não existia."""

    def test_pagamento_atrasado_gera_notificacao(self, client_as, cenario, db_session):
        pagamento = Payment(
            user_id=cenario["user"].id, property_id=cenario["prop"].id,
            tenant_id=cenario["tenant"].id, contract_id=cenario["contrato"].id,
            due_date=date.today() - timedelta(days=15),
            amount=2000, fine_amount=0, interest_amount=0, total_amount=2000,
            status="atrasado",
        )
        db_session.add(pagamento)
        db_session.flush()

        client: TestClient = client_as(cenario["user"].id)
        r = client.post("/api/v1/notifications/process-background-tasks/")
        assert r.status_code == 200, r.text
        assert r.json()["notifications_created"] >= 1

        notificacoes = client.get("/api/v1/notifications/").json()["items"]
        assert any(n["type"] == "payment_overdue" for n in notificacoes)

    def test_contrato_vincendo_gera_notificacao(self, client_as, cenario):
        """O contrato do cenário vence em 20 dias."""
        client: TestClient = client_as(cenario["user"].id)
        r = client.post("/api/v1/notifications/process-background-tasks/")
        assert r.status_code == 200, r.text

        notificacoes = client.get("/api/v1/notifications/").json()["items"]
        assert any(n["type"] == "contract_expiring" for n in notificacoes)

    def test_antispam_evita_repetir_o_mesmo_alerta(self, client_as, cenario):
        """
        Sem antispam, o job diário criaria um alerta por dia para o mesmo
        contrato até ele vencer, e o usuário aprenderia a ignorar o sino.
        """
        client: TestClient = client_as(cenario["user"].id)

        primeira = client.post("/api/v1/notifications/process-background-tasks/").json()
        segunda = client.post("/api/v1/notifications/process-background-tasks/").json()

        assert primeira["notifications_created"] >= 1
        assert segunda["notifications_created"] == 0, "alerta duplicado no mesmo dia"


class TestFiltrosCombinaveis:
    """M-04 — filtros encadeados com if/elif descartavam todos menos o primeiro."""

    @pytest.fixture
    def pagamentos(self, db_session, cenario):
        base = dict(
            user_id=cenario["user"].id, property_id=cenario["prop"].id,
            tenant_id=cenario["tenant"].id, contract_id=cenario["contrato"].id,
            amount=1000, fine_amount=0, interest_amount=0, total_amount=1000,
        )
        db_session.add_all([
            Payment(**base, due_date=date.today(), status="pendente"),
            Payment(**base, due_date=date.today(), status="atrasado"),
            Payment(**base, due_date=date.today(), status="pago"),
        ])
        db_session.flush()

    def test_property_id_e_status_combinam(self, client_as, cenario, pagamentos):
        client: TestClient = client_as(cenario["user"].id)
        r = client.get(
            f"/api/v1/payments/?property_id={cenario['prop'].id}&status=atrasado"
        )
        assert r.status_code == 200
        resultado = r.json()
        assert len(resultado) == 1, "o filtro de status foi descartado"
        assert resultado[0]["status"] == "atrasado"

    def test_paginacao_e_respeitada_com_filtro(self, client_as, cenario, pagamentos):
        """Os ramos de filtro ignoravam skip/limit e devolviam tudo."""
        client: TestClient = client_as(cenario["user"].id)
        r = client.get(f"/api/v1/payments/?property_id={cenario['prop'].id}&limit=2")
        assert r.status_code == 200
        assert len(r.json()) == 2


class TestContratosVincendos:
    """M-06 — contratos JÁ vencidos apareciam como 'vencendo em N dias'."""

    def test_contrato_vencido_nao_aparece_como_vincendo(
        self, client_as, cenario, db_session
    ):
        vencido = Contract(
            user_id=cenario["user"].id, title="Vencido",
            property_id=cenario["prop"].id, tenant_id=cenario["tenant"].id,
            start_date=date.today() - timedelta(days=400),
            end_date=date.today() - timedelta(days=30),  # já passou
            rent=2000, deposit=0, interest_rate=0, fine_rate=0, status="ativo",
        )
        db_session.add(vencido)
        db_session.flush()

        client: TestClient = client_as(cenario["user"].id)
        r = client.get("/api/v1/contracts/expiring?days_ahead=30")
        assert r.status_code == 200

        titulos = [c["title"] for c in r.json()]
        assert "Vencido" not in titulos, "contrato já vencido listado como vincendo"


class TestFusoHorario:
    """M-07 — `date.today()` (UTC) convivia com `datetime.now(BRT)`."""

    def test_hoje_brt_usa_o_fuso_de_sao_paulo(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo

        from src.core.tempo import hoje_brt

        esperado = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
        assert hoje_brt() == esperado

    def test_nenhum_modulo_usa_date_today_diretamente(self):
        """
        Guarda de regressão: `date.today()` devolve a data do fuso do processo
        (UTC no container), adiantando a virada do dia em 3 horas.
        """
        import pathlib

        infratores = []
        for arquivo in pathlib.Path("src").rglob("*.py"):
            if arquivo.name == "tempo.py":
                continue
            texto = arquivo.read_text(encoding="utf-8")
            for numero, linha in enumerate(texto.splitlines(), 1):
                if "date.today()" in linha and not linha.strip().startswith("#"):
                    infratores.append(f"{arquivo}:{numero}")

        assert not infratores, (
            "use `hoje_brt()` em vez de `date.today()`: " + ", ".join(infratores)
        )
