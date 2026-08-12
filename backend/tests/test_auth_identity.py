"""
Testes de identidade de conta (regressão do achado C-05).

A identidade local era resolvida por `users.email`, e `PUT /auth/me` permitia
trocar esse e-mail livremente — chave de identidade mutável, com potencial de
um usuário passar a resolver para o registro de outro.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.database import get_db
from src.security import get_current_user

UID_A = "33333333-3333-4333-8333-333333333333"
UID_B = "44444444-4444-4444-8444-444444444444"


@pytest.fixture
def client_as_supabase(db_session):
    """TestClient autenticado como uma identidade Supabase concreta."""

    def _client(uid: str, email: str) -> TestClient:
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_user] = lambda: {
            "id": uid, "email": email, "role": "authenticated", "payload": {},
        }
        return TestClient(app)

    yield _client
    app.dependency_overrides.clear()


@pytest.fixture
def usuarios(db_session, make_user):
    a = make_user("dono-a@imobly.com.br", UID_A)
    b = make_user("dono-b@imobly.com.br", UID_B)
    db_session.flush()
    return a, b


class TestTrocaDeEmailBloqueada:
    def test_nao_permite_assumir_email_de_outro_usuario(
        self, client_as_supabase, usuarios, db_session
    ):
        a, b = usuarios
        client = client_as_supabase(UID_A, a.email)

        response = client.put("/api/v1/auth/me", json={"email": b.email})

        assert response.status_code == 400
        db_session.refresh(a)
        db_session.refresh(b)
        assert a.email == "dono-a@imobly.com.br"
        assert b.email == "dono-b@imobly.com.br"

    def test_nao_permite_trocar_para_email_novo(self, client_as_supabase, usuarios, db_session):
        a, _ = usuarios
        client = client_as_supabase(UID_A, a.email)

        response = client.put("/api/v1/auth/me", json={"email": "outro@imobly.com.br"})

        assert response.status_code == 400
        db_session.refresh(a)
        assert a.email == "dono-a@imobly.com.br"

    def test_permite_atualizar_nome_completo(self, client_as_supabase, usuarios, db_session):
        a, _ = usuarios
        client = client_as_supabase(UID_A, a.email)

        response = client.put("/api/v1/auth/me", json={"full_name": "Nome Atualizado"})

        assert response.status_code == 200
        assert response.json()["full_name"] == "Nome Atualizado"

    def test_reenviar_o_proprio_email_nao_e_rejeitado(
        self, client_as_supabase, usuarios
    ):
        """O frontend reenvia o e-mail atual junto do nome — não deve quebrar."""
        a, _ = usuarios
        client = client_as_supabase(UID_A, a.email)

        response = client.put(
            "/api/v1/auth/me", json={"email": a.email, "full_name": "Outro Nome"}
        )

        assert response.status_code == 200


class TestResolucaoDeIdentidade:
    def test_perfil_resolve_pelo_uid_e_nao_pelo_email(
        self, client_as_supabase, usuarios, db_session
    ):
        """
        Mesmo que o token traga um e-mail divergente do registro local, o perfil
        devolvido deve ser o do `supabase_uid` — a chave imutável.
        """
        a, _ = usuarios
        client = client_as_supabase(UID_A, "email-antigo@imobly.com.br")

        response = client.get("/api/v1/auth/me")

        assert response.status_code == 200
        assert response.json()["id"] == str(a.id)
        assert response.json()["email"] == "dono-a@imobly.com.br"

    def test_conta_desativada_perde_acesso(self, db_session, make_user):
        """`is_active=False` deve barrar o acesso — antes era ignorado."""
        from src.security import get_current_user_local_id

        user = make_user("inativo@imobly.com.br", "55555555-5555-4555-8555-555555555555")
        user.is_active = False
        db_session.flush()

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_user] = lambda: {
            "id": "55555555-5555-4555-8555-555555555555",
            "email": "inativo@imobly.com.br", "role": "authenticated", "payload": {},
        }
        app.dependency_overrides.pop(get_current_user_local_id, None)
        try:
            client = TestClient(app)
            response = client.get("/api/v1/properties/")
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()
