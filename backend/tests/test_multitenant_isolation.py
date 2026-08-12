"""
Testes de isolamento multi-tenant (regressão dos achados C-01, C-02 e A-06).

O cenário é sempre o mesmo: o usuário A autenticado tenta referenciar entidades
do usuário B. Toda tentativa deve resultar em 404 — nunca em escrita bem
sucedida, e nunca em 403 (que confirmaria a existência do registro alheio).
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from src.contracts.models import Contract
from src.properties.models import Property
from src.tenants.models import Tenant


@pytest.fixture
def two_tenants(db_session, make_user):
    """
    Monta dois usuários, cada um com imóvel, inquilino e contrato próprios.
    Devolve um dicionário com os ids relevantes.
    """
    user_a = make_user("a@imobly.test", "11111111-1111-4111-8111-111111111111")
    user_b = make_user("b@imobly.test", "22222222-2222-4222-8222-222222222222")

    def _property(owner_id: int, name: str) -> Property:
        prop = Property(
            user_id=owner_id, name=name, address="Rua X, 1", neighborhood="Centro",
            city="São Paulo", state="SP", zip_code="01000-000", type="apartment",
            area=70, bedrooms=2, bathrooms=1, parking_spaces=1, rent=2000,
            status="vacant",
        )
        db_session.add(prop)
        db_session.flush()
        return prop

    def _tenant(owner_id: int, email: str, cpf: str) -> Tenant:
        tenant = Tenant(
            user_id=owner_id, name="Inquilino", email=email, phone="11999999999",
            cpf_cnpj=cpf, profession="Analista",
        )
        db_session.add(tenant)
        db_session.flush()
        return tenant

    def _contract(owner_id: int, prop_id: int, tenant_id: int) -> Contract:
        contract = Contract(
            user_id=owner_id, title="Locação", property_id=prop_id, tenant_id=tenant_id,
            start_date=date.today(), end_date=date.today() + timedelta(days=365),
            rent=2000, deposit=2000, interest_rate=1, fine_rate=2, status="ativo",
        )
        db_session.add(contract)
        db_session.flush()
        return contract

    prop_a = _property(user_a.id, "Imóvel do A")
    prop_b = _property(user_b.id, "Imóvel do B")
    tenant_a = _tenant(user_a.id, "ta@imobly.test", "11111111111")
    tenant_b = _tenant(user_b.id, "tb@imobly.test", "22222222222")
    contract_a = _contract(user_a.id, prop_a.id, tenant_a.id)
    contract_b = _contract(user_b.id, prop_b.id, tenant_b.id)
    db_session.flush()

    return {
        "user_a": user_a.id, "user_b": user_b.id,
        "prop_a": prop_a.id, "prop_b": prop_b.id,
        "tenant_a": tenant_a.id, "tenant_b": tenant_b.id,
        "contract_a": contract_a.id, "contract_b": contract_b.id,
    }


class TestContractIsolation:
    """C-01 e C-02 — o ciclo de vida do contrato tocava imóveis de terceiros."""

    def test_nao_cria_contrato_sobre_imovel_alheio(self, client_as, two_tenants, db_session):
        ids = two_tenants
        client: TestClient = client_as(ids["user_a"])

        response = client.post("/api/v1/contracts/", json={
            "title": "Invasão", "property_id": ids["prop_b"], "tenant_id": ids["tenant_a"],
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=365)),
            "rent": 1000, "deposit": 0, "interest_rate": 0, "fine_rate": 0,
            "status": "ativo",
        })

        assert response.status_code == 404
        # E o imóvel da vítima permanece intocado
        prop_b = db_session.query(Property).filter(Property.id == ids["prop_b"]).first()
        assert prop_b.status == "vacant"
        assert prop_b.tenant_id is None

    def test_nao_cria_contrato_com_inquilino_alheio(self, client_as, two_tenants):
        ids = two_tenants
        client: TestClient = client_as(ids["user_a"])

        response = client.post("/api/v1/contracts/", json={
            "title": "Invasão", "property_id": ids["prop_a"], "tenant_id": ids["tenant_b"],
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=365)),
            "rent": 1000, "deposit": 0, "interest_rate": 0, "fine_rate": 0,
            "status": "ativo",
        })

        assert response.status_code == 404

    def test_nao_remaneja_contrato_para_imovel_alheio(self, client_as, two_tenants):
        ids = two_tenants
        client: TestClient = client_as(ids["user_a"])

        response = client.put(
            f"/api/v1/contracts/{ids['contract_a']}",
            json={"property_id": ids["prop_b"]},
        )

        assert response.status_code == 404

    def test_nao_acessa_contrato_alheio(self, client_as, two_tenants):
        ids = two_tenants
        client: TestClient = client_as(ids["user_a"])
        assert client.get(f"/api/v1/contracts/{ids['contract_b']}").status_code == 404


class TestPaymentIsolation:
    """C-01 — FKs de pagamento chegavam cruas do payload."""

    def _payload(self, ids, **overrides):
        payload = {
            "property_id": ids["prop_a"], "tenant_id": ids["tenant_a"],
            "contract_id": ids["contract_a"], "due_date": str(date.today()),
            "amount": 1000, "fine_amount": 0, "total_amount": 1000,
            "status": "pendente",
        }
        payload.update(overrides)
        return payload

    @pytest.mark.parametrize("campo,chave_alheia", [
        ("property_id", "prop_b"),
        ("tenant_id", "tenant_b"),
        ("contract_id", "contract_b"),
    ])
    def test_nao_cria_pagamento_com_fk_alheia(self, client_as, two_tenants, campo, chave_alheia):
        ids = two_tenants
        client: TestClient = client_as(ids["user_a"])

        response = client.post(
            "/api/v1/payments/",
            json=self._payload(ids, **{campo: ids[chave_alheia]}),
        )

        assert response.status_code == 404, f"{campo} alheio foi aceito"

    def test_cria_pagamento_com_fks_proprias(self, client_as, two_tenants):
        ids = two_tenants
        client: TestClient = client_as(ids["user_a"])
        response = client.post("/api/v1/payments/", json=self._payload(ids))
        assert response.status_code == 201


class TestExpenseAndPropertyIsolation:
    """C-01 — despesas e o vínculo property.tenant_id."""

    def test_nao_cria_despesa_em_imovel_alheio(self, client_as, two_tenants):
        ids = two_tenants
        client: TestClient = client_as(ids["user_a"])

        response = client.post("/api/v1/expenses/", json={
            "type": "manutencao", "property_id": ids["prop_b"], "category": "reparo",
            "description": "Invasão", "amount": 100, "date": str(date.today()),
            "status": "pending",
        })

        assert response.status_code == 404

    def test_nao_vincula_inquilino_alheio_ao_proprio_imovel(self, client_as, two_tenants):
        ids = two_tenants
        client: TestClient = client_as(ids["user_a"])

        response = client.put(
            f"/api/v1/properties/{ids['prop_a']}",
            json={"tenant_id": ids["tenant_b"]},
        )

        assert response.status_code == 404


class TestUploadsNaoExpostos:
    """A-06 — o mount público de /uploads foi removido."""

    def test_uploads_nao_e_servido_estaticamente(self, client_as, two_tenants):
        client: TestClient = client_as(two_tenants["user_a"])
        assert client.get("/uploads/qualquer-arquivo.pdf").status_code == 404
