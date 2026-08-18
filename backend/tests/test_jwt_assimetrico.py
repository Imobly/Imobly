"""
Validação de tokens assinados com chave assimétrica (ES256).

Regressão de um defeito que só apareceu ao trocar o projeto do Supabase:
projetos novos assinam os access tokens com ES256 e publicam a chave pública
via JWKS. O backend só sabia validar HS256 com segredo compartilhado, então o
login devolvia 200 e TODA requisição autenticada depois dele respondia 401 —
sintoma que parece "sessão que não persiste", não "algoritmo não suportado".

A suíte não pegava porque `get_current_user` é sempre substituído por
dependency override nos outros testes; `verify_jwt_token` nunca era exercitado
de verdade.
"""

import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from src.core import jwks

EMISSOR = "https://projeto-teste.supabase.co"


@pytest.fixture
def par_de_chaves():
    """Gera um par ES256 e devolve (chave_privada, jwk_publico, kid)."""
    privada = ec.generate_private_key(ec.SECP256R1())
    publica = privada.public_key()

    from jwt.algorithms import ECAlgorithm

    jwk_publico = json.loads(ECAlgorithm.to_jwk(publica))
    kid = "kid-de-teste"
    jwk_publico["kid"] = kid
    jwk_publico["alg"] = "ES256"
    jwk_publico["use"] = "sig"
    return privada, jwk_publico, kid


@pytest.fixture(autouse=True)
def cache_limpo():
    jwks.limpar_cache()
    yield
    jwks.limpar_cache()


def _emitir(privada, kid, **extras):
    claims = {
        "sub": "11111111-1111-4111-8111-111111111111",
        "email": "usuario@imobly.com.br",
        "aud": "authenticated",
        "iss": f"{EMISSOR}/auth/v1",
        "exp": int(time.time()) + 3600,
        "role": "authenticated",
    }
    claims.update(extras)
    return jwt.encode(claims, privada, algorithm="ES256", headers={"kid": kid})


class TestPyJWTComCrypto:
    def test_algoritmos_assimetricos_disponiveis(self):
        """
        Sem o extra `PyJWT[crypto]`, `jwt.algorithms` nem expõe ECAlgorithm —
        e o sintoma vira um 401 genérico, longe da causa. Este teste falha
        alto se a dependência for removida de novo.
        """
        from jwt.algorithms import ECAlgorithm, RSAAlgorithm  # noqa: F401

        assert "ES256" in jwt.algorithms.get_default_algorithms()


class TestValidacaoES256:
    def test_token_valido_e_aceito(self, par_de_chaves, monkeypatch):
        privada, jwk_publico, kid = par_de_chaves
        monkeypatch.setattr(jwks, "_buscar_jwks", lambda url: {"keys": [jwk_publico]})

        chave = jwks.obter_chave_publica(EMISSOR, kid)
        assert chave is not None

        token = _emitir(privada, kid)
        claims = jwt.decode(
            token, chave, algorithms=["ES256"],
            audience="authenticated", issuer=f"{EMISSOR}/auth/v1",
        )
        assert claims["email"] == "usuario@imobly.com.br"

    def test_kid_desconhecido_devolve_none(self, par_de_chaves, monkeypatch):
        _, jwk_publico, _ = par_de_chaves
        monkeypatch.setattr(jwks, "_buscar_jwks", lambda url: {"keys": [jwk_publico]})

        assert jwks.obter_chave_publica(EMISSOR, "kid-que-nao-existe") is None

    def test_token_de_outra_chave_e_rejeitado(self, par_de_chaves, monkeypatch):
        """Assinatura de um par diferente não pode passar."""
        _, jwk_publico, kid = par_de_chaves
        monkeypatch.setattr(jwks, "_buscar_jwks", lambda url: {"keys": [jwk_publico]})
        chave = jwks.obter_chave_publica(EMISSOR, kid)

        intrusa = ec.generate_private_key(ec.SECP256R1())
        token = _emitir(intrusa, kid)

        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, chave, algorithms=["ES256"],
                       audience="authenticated", issuer=f"{EMISSOR}/auth/v1")

    def test_emissor_divergente_e_rejeitado(self, par_de_chaves, monkeypatch):
        privada, jwk_publico, kid = par_de_chaves
        monkeypatch.setattr(jwks, "_buscar_jwks", lambda url: {"keys": [jwk_publico]})
        chave = jwks.obter_chave_publica(EMISSOR, kid)

        token = _emitir(privada, kid, iss="https://outro-projeto.supabase.co/auth/v1")

        with pytest.raises(jwt.InvalidIssuerError):
            jwt.decode(token, chave, algorithms=["ES256"],
                       audience="authenticated", issuer=f"{EMISSOR}/auth/v1")


class TestCacheDoJWKS:
    def test_jwks_nao_e_buscado_a_cada_chamada(self, par_de_chaves, monkeypatch):
        """
        Buscar o JWKS por requisição adicionaria um round-trip HTTP ao caminho
        de autenticação de TODA chamada.
        """
        _, jwk_publico, kid = par_de_chaves
        buscas = {"n": 0}

        def _contar(url):
            buscas["n"] += 1
            return {"keys": [jwk_publico]}

        monkeypatch.setattr(jwks, "_buscar_jwks", _contar)

        for _ in range(5):
            assert jwks.obter_chave_publica(EMISSOR, kid) is not None
        assert buscas["n"] == 1, f"JWKS buscado {buscas['n']}x — cache não funcionou"

    def test_falha_de_rede_nao_derruba_chave_ja_em_cache(self, par_de_chaves, monkeypatch):
        """Queda momentânea do endpoint não deve invalidar a autenticação."""
        _, jwk_publico, kid = par_de_chaves
        monkeypatch.setattr(jwks, "_buscar_jwks", lambda url: {"keys": [jwk_publico]})
        assert jwks.obter_chave_publica(EMISSOR, kid) is not None

        def _falhar(url):
            raise RuntimeError("endpoint fora do ar")

        monkeypatch.setattr(jwks, "_buscar_jwks", _falhar)
        assert jwks.obter_chave_publica(EMISSOR, kid) is not None
