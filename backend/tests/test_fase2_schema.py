"""
Testes de regressão da Fase 2 (achados C-03, C-04, A-11 e A-12).

Cada classe cobre um defeito que o schema real tinha e os modelos não
refletiam — a classe de erro que só aparecia em runtime, contra o banco.
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from src.contracts.models import Contract
from src.properties.models import Property
from src.tenants.models import Tenant


@pytest.fixture
def usuario(db_session, make_user):
    u = make_user("fase2@imobly.com.br", "66666666-6666-4666-8666-666666666666")
    db_session.flush()
    return u


class TestNotificacoesOperantes:
    """
    C-03 — o repositório consultava `read_status`/`related_id`, que não
    existiam no banco: todo endpoint respondia 500.
    """

    def test_listar_notificacoes_responde_200(self, client_as, usuario):
        client: TestClient = client_as(usuario.id)
        r = client.get("/api/v1/notifications/")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_criar_e_listar_notificacao(self, client_as, usuario):
        client: TestClient = client_as(usuario.id)

        criada = client.post("/api/v1/notifications/", json={
            "type": "payment_overdue",
            "title": "Pagamento atrasado",
            "message": "O aluguel venceu.",
            "priority": "high",
            "related_id": "42",
            "related_type": "payment",
            "action_required": True,
        })
        assert criada.status_code == 201, criada.text

        corpo = criada.json()
        # PK textual (UUID), não inteiro — alinhada ao banco e a `expenses`
        assert isinstance(corpo["id"], str) and len(corpo["id"]) == 36
        assert corpo["read_status"] is False
        assert corpo["priority"] == "high"

        listagem = client.get("/api/v1/notifications/")
        assert listagem.status_code == 200
        assert listagem.json()["total"] == 1

    def test_marcar_como_lida_e_contar_nao_lidas(self, client_as, usuario):
        client: TestClient = client_as(usuario.id)
        nid = client.post("/api/v1/notifications/", json={
            "type": "reminder", "title": "Lembrete", "message": "Teste",
        }).json()["id"]

        assert client.get("/api/v1/notifications/count/unread/").json()["unread_count"] == 1

        lida = client.put(f"/api/v1/notifications/{nid}/read/")
        assert lida.status_code == 200
        assert lida.json()["read_status"] is True

        assert client.get("/api/v1/notifications/count/unread/").json()["unread_count"] == 0

    def test_antispam_consulta_related_id_sem_erro(self, db_session, usuario):
        """`has_recent_notification` usa colunas que antes não existiam."""
        from src.notifications.repository import NotificationRepository

        repo = NotificationRepository(db_session)
        assert repo.has_recent_notification(usuario.id, "42", "payment_overdue") is False


class TestUnicidadeInquilinoPorLocador:
    """C-04 — UNIQUE global impedia dois locadores de ter o mesmo inquilino."""

    def _payload(self, **over):
        base = {
            "name": "Fulano", "email": "mesmo@imobly.com.br", "phone": "11999999999",
            "cpf_cnpj": "12345678901", "profession": "Analista",
        }
        base.update(over)
        return base

    def test_dois_locadores_podem_ter_o_mesmo_inquilino(
        self, client_as, db_session, make_user
    ):
        a = make_user("loc-a@imobly.com.br", "77777777-7777-4777-8777-777777777777")
        b = make_user("loc-b@imobly.com.br", "88888888-8888-4888-8888-888888888888")
        db_session.flush()

        r1 = client_as(a.id).post("/api/v1/tenants/", json=self._payload())
        assert r1.status_code == 201, r1.text

        # Mesmo e-mail e CPF, outro locador: deve ser permitido.
        r2 = client_as(b.id).post("/api/v1/tenants/", json=self._payload())
        assert r2.status_code == 201, r2.text

    def test_duplicata_no_mesmo_locador_e_rejeitada(self, client_as, usuario):
        client: TestClient = client_as(usuario.id)
        assert client.post("/api/v1/tenants/", json=self._payload()).status_code == 201

        dup = client.post("/api/v1/tenants/", json=self._payload(cpf_cnpj="99999999999"))
        assert dup.status_code in (400, 409)

    def test_email_duplicado_ignorando_maiusculas(self, client_as, usuario):
        """O índice é sobre lower(email); a checagem precisa acompanhar."""
        client: TestClient = client_as(usuario.id)
        assert client.post("/api/v1/tenants/", json=self._payload()).status_code == 201

        dup = client.post("/api/v1/tenants/", json=self._payload(
            email="MESMO@imobly.com.br", cpf_cnpj="99999999999",
        ))
        assert dup.status_code in (400, 409), "variação de caixa burlou a unicidade"


class TestPoliticasOnDelete:
    """A-11 — as políticas existiam no modelo, mas não no banco."""

    @pytest.fixture
    def cenario(self, db_session, usuario):
        prop = Property(
            user_id=usuario.id, name="Imóvel", address="Rua X, 1", neighborhood="Centro",
            city="São Paulo", state="SP", zip_code="01000-000", type="apartment",
            area=70, bedrooms=2, bathrooms=1, parking_spaces=1, rent=2000, status="vacant",
        )
        tenant = Tenant(
            user_id=usuario.id, name="Inquilino", email="inq@imobly.com.br",
            phone="11999999999", cpf_cnpj="11122233344", profession="Analista",
        )
        db_session.add_all([prop, tenant])
        db_session.flush()

        contrato = Contract(
            user_id=usuario.id, title="Locação", property_id=prop.id, tenant_id=tenant.id,
            start_date=date.today(), end_date=date.today() + timedelta(days=365),
            rent=2000, deposit=2000, interest_rate=1, fine_rate=2, status="ativo",
        )
        db_session.add(contrato)
        db_session.flush()
        return {"prop": prop, "tenant": tenant, "contrato": contrato, "user": usuario}

    def test_apagar_inquilino_com_contrato_devolve_409_e_nao_500(self, client_as, cenario):
        """RESTRICT: o histórico locatício não some silenciosamente."""
        client: TestClient = client_as(cenario["user"].id)
        r = client.delete(f"/api/v1/tenants/{cenario['tenant'].id}")
        assert r.status_code == 409, f"esperado 409, veio {r.status_code}: {r.text}"
        assert "contrato" in r.json()["detail"].lower()

    def test_apagar_imovel_cascateia_contratos(self, db_session, cenario):
        """CASCADE: contrato não existe sem o imóvel."""
        contrato_id = cenario["contrato"].id
        # `tenants.contract_id` é SET NULL; limpe o vínculo reverso primeiro
        # para que o CASCADE do imóvel possa remover o contrato.
        db_session.delete(cenario["prop"])
        db_session.flush()

        restante = db_session.execute(
            text("SELECT count(*) FROM contracts WHERE id = :i"), {"i": contrato_id}
        ).scalar()
        assert restante == 0, "contrato sobreviveu ao imóvel — CASCADE não aplicado"


class TestTimestampsNaoNulos:
    """A-12 — timestamps nulos faziam a listagem inteira responder 500."""

    def test_insercao_fora_do_orm_recebe_timestamps_do_banco(self, db_session, usuario):
        """
        Simula seed/importação em SQL puro: sem DEFAULT no banco, created_at
        ficava nulo e o response model quebrava a listagem toda.
        """
        db_session.execute(
            text(
                """
                INSERT INTO properties
                    (user_id, name, address, neighborhood, city, state, zip_code,
                     type, area, bedrooms, bathrooms, rent, status)
                VALUES
                    (:u, 'Seed', 'Rua Y, 2', 'Centro', 'SP', 'SP', '01000-000',
                     'house', 100, 3, 2, 3000, 'vacant')
                """
            ),
            {"u": usuario.id},
        )
        db_session.flush()

        linha = db_session.execute(
            text(
                "SELECT created_at, updated_at FROM properties "
                "WHERE user_id = :u AND name = 'Seed'"
            ),
            {"u": usuario.id},
        ).first()

        assert linha.created_at is not None, "created_at nulo — DEFAULT ausente"
        assert linha.updated_at is not None, "updated_at nulo — DEFAULT ausente"

    def test_listagem_funciona_apos_insercao_em_sql_puro(self, client_as, db_session, usuario):
        db_session.execute(
            text(
                """
                INSERT INTO properties
                    (user_id, name, address, neighborhood, city, state, zip_code,
                     type, area, bedrooms, bathrooms, rent, status)
                VALUES
                    (:u, 'Seed', 'Rua Y, 2', 'Centro', 'SP', 'SP', '01000-000',
                     'house', 100, 3, 2, 3000, 'vacant')
                """
            ),
            {"u": usuario.id},
        )
        db_session.flush()

        r = client_as(usuario.id).get("/api/v1/properties/")
        assert r.status_code == 200, r.text
        assert len(r.json()) == 1
