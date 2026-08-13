"""
Testes de regressão da Fase 4 (A-04, A-05, A-10).

A-13 (checagens de build) e A-14 (scheduler duplicado) não são cobertos aqui:
o primeiro é verificado por `tsc --noEmit` no frontend, o segundo depende de
múltiplos processos concorrentes, o que a suíte não reproduz de forma
confiável.
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from src.contracts.models import Contract
from src.properties.models import Property
from src.tenants.models import Tenant


@pytest.fixture
def cenario(db_session, make_user):
    user = make_user("fase4@imobly.com.br", "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    db_session.flush()

    prop = Property(
        user_id=user.id, name="Imóvel", address="Rua W, 4", neighborhood="Centro",
        city="São Paulo", state="SP", zip_code="01000-000", type="apartment",
        area=70, bedrooms=2, bathrooms=1, parking_spaces=1, rent=2000, status="vacant",
    )
    tenant = Tenant(
        user_id=user.id, name="Inquilino", email="f4@imobly.com.br",
        phone="11999999999", cpf_cnpj="99988877766", profession="Analista",
    )
    db_session.add_all([prop, tenant])
    db_session.flush()
    return {"user": user, "prop": prop, "tenant": tenant}


class TestDuplaLocacao:
    """A-04 — nada impedia dois contratos ativos sobrepostos no mesmo imóvel."""

    def _contrato(self, cenario, inicio: date, fim: date, titulo="C"):
        return {
            "title": titulo,
            "property_id": cenario["prop"].id,
            "tenant_id": cenario["tenant"].id,
            "start_date": str(inicio),
            "end_date": str(fim),
            "rent": 2000, "deposit": 0, "interest_rate": 0, "fine_rate": 0,
            "status": "ativo",
        }

    def test_periodo_sobreposto_e_rejeitado_com_409(self, client_as, cenario):
        client: TestClient = client_as(cenario["user"].id)
        hoje = date.today()

        primeiro = client.post(
            "/api/v1/contracts/",
            json=self._contrato(cenario, hoje, hoje + timedelta(days=365), "A"),
        )
        assert primeiro.status_code == 201, primeiro.text

        # Começa no meio da vigência do primeiro
        segundo = client.post(
            "/api/v1/contracts/",
            json=self._contrato(
                cenario, hoje + timedelta(days=180), hoje + timedelta(days=545), "B"
            ),
        )
        assert segundo.status_code == 409, (
            f"dupla locação foi aceita ({segundo.status_code})"
        )
        assert "já existe um contrato ativo" in segundo.json()["detail"].lower()

    def test_periodos_sequenciais_sao_permitidos(self, client_as, cenario):
        """Locação seguinte, começando depois do fim da anterior."""
        client: TestClient = client_as(cenario["user"].id)
        hoje = date.today()

        a = client.post(
            "/api/v1/contracts/",
            json=self._contrato(cenario, hoje, hoje + timedelta(days=364), "A"),
        )
        assert a.status_code == 201, a.text

        b = client.post(
            "/api/v1/contracts/",
            json=self._contrato(
                cenario, hoje + timedelta(days=365), hoje + timedelta(days=700), "B"
            ),
        )
        assert b.status_code == 201, b.text

    def test_contrato_inativo_nao_bloqueia_novo(self, client_as, cenario, db_session):
        """A constraint só considera contratos ativos."""
        client: TestClient = client_as(cenario["user"].id)
        hoje = date.today()

        encerrado = Contract(
            user_id=cenario["user"].id, title="Encerrado",
            property_id=cenario["prop"].id, tenant_id=cenario["tenant"].id,
            start_date=hoje, end_date=hoje + timedelta(days=365),
            rent=2000, deposit=0, interest_rate=0, fine_rate=0, status="inativo",
        )
        db_session.add(encerrado)
        db_session.flush()

        novo = client.post(
            "/api/v1/contracts/",
            json=self._contrato(cenario, hoje, hoje + timedelta(days=365), "Novo"),
        )
        assert novo.status_code == 201, novo.text


class TestCacheDeIdentidade:
    """A-05 — cache sem teto, sem expiração e sem invalidação."""

    def test_cache_tem_teto_e_expiracao(self):
        from src.security import _local_id_cache

        assert _local_id_cache.maxsize == 10_000, "cache sem teto volta a vazar"
        assert _local_id_cache.ttl == 300, "sem TTL, mudanças no banco nunca refletem"

    def test_invalidacao_remove_entrada(self):
        from src.security import _local_id_cache, invalidar_cache_de_identidade

        _local_id_cache["uid-teste"] = 123
        invalidar_cache_de_identidade("uid-teste")
        assert "uid-teste" not in _local_id_cache

    def test_invalidacao_total(self):
        from src.security import _local_id_cache, invalidar_cache_de_identidade

        _local_id_cache["a"] = 1
        _local_id_cache["b"] = 2
        invalidar_cache_de_identidade()
        assert len(_local_id_cache) == 0


class TestIndices:
    """A-10 — o banco não tinha índice nenhum além das PKs."""

    @pytest.mark.parametrize("indice", [
        "ix_payments_user_status",
        "ix_payments_user_due_date",
        "ix_payments_pagos_por_data",
        "ix_contracts_user_status",
        "ix_contracts_ativos_fim",
        "ix_expenses_user_date",
        "ix_properties_user_status",
    ])
    def test_indice_existe(self, db_session, indice):
        encontrado = db_session.execute(
            text("SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname=:n"),
            {"n": indice},
        ).scalar()
        assert encontrado == 1, f"índice ausente: {indice}"

    def test_consulta_de_inadimplencia_e_indexada(self, db_session, cenario):
        """
        Confere no plano de execução que o filtro por dono é atendido por
        índice, e não por sequential scan — o comportamento antes desta fase,
        quando o banco não tinha índice algum além das PKs.

        Não exige um índice específico: vários começam por `user_id` e o
        planejador escolhe entre eles conforme as estatísticas. O que importa
        é existir algum caminho indexado.
        """
        plano = db_session.execute(
            text(
                "EXPLAIN SELECT * FROM payments "
                "WHERE user_id = :u AND status = 'atrasado'"
            ),
            {"u": cenario["user"].id},
        ).scalars().all()
        texto = " ".join(plano)

        assert "Index Scan" in texto or "Bitmap" in texto, (
            f"consulta não usou índice — plano: {texto}"
        )


class TestStatusDoInquilino:
    """
    A checagem de tipos do frontend revelou que a API nunca devolvia
    `tenant.status`, então a UI exibia TODO inquilino como "inativo".
    """

    def test_inquilino_sem_contrato_e_inativo(self, client_as, cenario):
        client: TestClient = client_as(cenario["user"].id)
        r = client.get(f"/api/v1/tenants/{cenario['tenant'].id}")
        assert r.status_code == 200
        assert r.json()["status"] == "inativo"

    def test_inquilino_com_contrato_ativo_e_ativo(self, client_as, cenario, db_session):
        contrato = Contract(
            user_id=cenario["user"].id, title="Locação",
            property_id=cenario["prop"].id, tenant_id=cenario["tenant"].id,
            start_date=date.today(), end_date=date.today() + timedelta(days=365),
            rent=2000, deposit=0, interest_rate=0, fine_rate=0, status="ativo",
        )
        db_session.add(contrato)
        db_session.flush()
        cenario["tenant"].contract_id = contrato.id
        db_session.flush()

        client: TestClient = client_as(cenario["user"].id)
        r = client.get(f"/api/v1/tenants/{cenario['tenant'].id}")
        assert r.status_code == 200
        assert r.json()["status"] == "ativo"

    def test_listagem_traz_status(self, client_as, cenario):
        client: TestClient = client_as(cenario["user"].id)
        r = client.get("/api/v1/tenants/")
        assert r.status_code == 200
        assert all("status" in t for t in r.json())
