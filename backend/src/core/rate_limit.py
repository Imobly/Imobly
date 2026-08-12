"""
Rate limiting das superfícies de autenticação.

`/login`, `/register` e `/change-password` não tinham nenhum throttling.
Como `/login` e `/change-password` chamam `sign_in_with_password` a cada
requisição, o problema é duplo: força bruta de credenciais e amplificação de
custo/quota contra o Supabase — um atacante consome a cota do projeto sem
nunca acertar uma senha.

O limite é por IP **e** por identificador. Só por IP, um atacante atrás de
CGNAT/proxy rotativo escapa; só por identificador, dá para varrer contas
diferentes à vontade. As duas chaves juntas fecham os dois caminhos.

Armazenamento em memória por padrão: suficiente para uma instância, mas cada
réplica passa a ter seu próprio contador (N réplicas = N× o limite). Defina
`RATE_LIMIT_STORAGE_URI` (ex.: `redis://host:6379`) para compartilhar o estado
quando houver mais de uma instância.
"""

from __future__ import annotations

import logging
import os

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")

# Desligar só é aceitável em teste — a suíte dispara muitas requisições
# seguidas de propósito e não deve esbarrar no limite.
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"


def chave_por_ip_e_identificador(request: Request) -> str:
    """
    Compõe a chave com o IP e, quando disponível, o identificador da tentativa.

    O corpo da requisição é lido pelo handler, não aqui — o identificador é
    publicado em `request.state` pela rota antes de a contagem ser consultada.
    """
    ip = get_remote_address(request)
    identificador = getattr(request.state, "rate_limit_identity", None)
    return f"{ip}:{identificador}" if identificador else ip


limiter = Limiter(
    key_func=chave_por_ip_e_identificador,
    storage_uri=_STORAGE_URI,
    enabled=RATE_LIMIT_ENABLED,
    # Cabeçalhos padrão ajudam clientes legítimos a se comportarem.
    headers_enabled=True,
)

if not RATE_LIMIT_ENABLED:
    logger.warning("Rate limiting DESATIVADO (RATE_LIMIT_ENABLED=false)")
elif _STORAGE_URI.startswith("memory://"):
    logger.warning(
        "Rate limiting em memória: com mais de uma réplica cada uma terá seu "
        "próprio contador. Configure RATE_LIMIT_STORAGE_URI para compartilhar."
    )

# ── Limites ──
# Login é o alvo clássico de força bruta; o limite é apertado porque usuário
# legítimo raramente erra a senha mais que algumas vezes por minuto.
LIMITE_LOGIN = "5/minute"
# Registro cria conta no Supabase (custo e quota); cadência humana é baixa.
LIMITE_REGISTRO = "3/hour"
# Troca de senha exige reautenticação, então é um oráculo de senha atual.
LIMITE_TROCA_SENHA = "5/hour"
