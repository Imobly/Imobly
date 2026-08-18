"""
Chaves públicas de assinatura do Supabase (JWKS).

Projetos novos do Supabase assinam os access tokens com chave ASSIMÉTRICA
(ES256 por padrão) e publicam a chave pública em
`{SUPABASE_URL}/auth/v1/.well-known/jwks.json`. O modelo antigo — HS256 com o
`SUPABASE_JWT_SECRET` compartilhado — continua valendo para projetos legados.

Este módulo resolve a chave pública correta a partir do `kid` do cabeçalho do
token, com cache: buscar o JWKS a cada requisição adicionaria um round-trip
HTTP ao caminho de autenticação de TODAS as chamadas.

O cache é invalidado sob demanda quando aparece um `kid` desconhecido — é
assim que a rotação de chaves do Supabase é absorvida sem reiniciar a
aplicação. Um TTL sozinho não bastaria: entre a rotação e o vencimento do TTL,
todo token novo seria rejeitado.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

# Janela mínima entre buscas forçadas. Sem ela, um token com `kid` inválido
# (forjado ou de outro projeto) dispararia uma requisição ao Supabase por
# tentativa — um vetor de amplificação barato para quem quisesse abusar.
_INTERVALO_MINIMO_ENTRE_BUSCAS = 30.0

# Renovação preventiva: mesmo sem `kid` desconhecido, o JWKS é reconsultado
# de tempos em tempos.
_TTL_DO_CACHE = 600.0

_lock = threading.Lock()
_cache: Dict[str, Any] = {}          # kid -> chave pública já convertida
_buscado_em: float = 0.0


def _buscar_jwks(url_do_projeto: str) -> Dict[str, Any]:
    endpoint = f"{url_do_projeto.rstrip('/')}/auth/v1/.well-known/jwks.json"
    resposta = httpx.get(endpoint, timeout=10)
    resposta.raise_for_status()
    return resposta.json()


def _converter(jwk: Dict[str, Any]):
    """
    Converte uma entrada JWK no objeto de chave pública que o PyJWT aceita.

    `jwt.algorithms` só expõe ECAlgorithm/RSAAlgorithm quando o PyJWT foi
    instalado com o extra `[crypto]`. Sem ele o import falha, e o erro precisa
    dizer isso — não virar um genérico "formato não suportado", que manda quem
    está depurando investigar o JWKS do Supabase em vez das dependências.
    """
    import json

    try:
        from jwt.algorithms import ECAlgorithm, RSAAlgorithm
    except ImportError as exc:
        raise RuntimeError(
            "PyJWT sem suporte a criptografia assimétrica. Instale com o extra: "
            "PyJWT[crypto]. Sem ele, tokens ES256/RS256 do Supabase não podem "
            "ser validados."
        ) from exc

    tipo = jwk.get("kty")
    if tipo == "EC":
        return ECAlgorithm.from_jwk(json.dumps(jwk))
    if tipo == "RSA":
        return RSAAlgorithm.from_jwk(json.dumps(jwk))
    raise ValueError(f"tipo de chave não suportado: {tipo}")


def _recarregar(url_do_projeto: str) -> None:
    """Rebusca o JWKS e substitui o cache. Chamado com o lock já adquirido."""
    global _buscado_em

    dados = _buscar_jwks(url_do_projeto)
    novo: Dict[str, Any] = {}
    for jwk in dados.get("keys", []):
        kid = jwk.get("kid")
        if not kid:
            continue
        try:
            novo[kid] = _converter(jwk)
        except RuntimeError:
            # Dependência ausente: não é problema desta chave e nenhuma outra
            # vai funcionar. Propaga em vez de mascarar como chave inválida.
            raise
        except Exception as exc:
            logger.warning("Chave JWKS ignorada (kid=%s): %s", kid, exc)

    _cache.clear()
    _cache.update(novo)
    _buscado_em = time.monotonic()
    logger.info("JWKS carregado: %d chave(s) — kids=%s", len(novo), list(novo))


def obter_chave_publica(url_do_projeto: str, kid: str) -> Optional[Any]:
    """
    Devolve a chave pública correspondente ao `kid`, ou None se não existir.

    Busca o JWKS quando o cache está vazio, expirado, ou quando o `kid` pedido
    não está nele — este último caso é o que absorve rotação de chaves.
    """
    global _buscado_em

    with _lock:
        chave = _cache.get(kid)
        expirado = (time.monotonic() - _buscado_em) > _TTL_DO_CACHE

        if chave is not None and not expirado:
            return chave

        # Rebusca só se o cache estiver frio/expirado OU o kid for desconhecido,
        # respeitando o intervalo mínimo para não virar amplificador.
        pode_buscar = (time.monotonic() - _buscado_em) > _INTERVALO_MINIMO_ENTRE_BUSCAS
        if not _cache or expirado or (chave is None and pode_buscar):
            try:
                _recarregar(url_do_projeto)
            except Exception as exc:
                logger.error("Falha ao buscar JWKS: %s", exc)
                # Com o cache ainda válido, seguimos com o que temos: uma queda
                # momentânea do endpoint não deve derrubar a autenticação.
                return _cache.get(kid)

        return _cache.get(kid)


def limpar_cache() -> None:
    """Descarta o cache (usado em teste)."""
    global _buscado_em
    with _lock:
        _cache.clear()
        _buscado_em = 0.0
