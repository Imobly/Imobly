"""
Configuração de logging da aplicação.

Existe porque o projeto não configurava logging em lugar nenhum: sem handler
no root logger, o nível efetivo era WARNING e TODA chamada `logger.info(...)`
do código era descartada em silêncio. Só os loggers do próprio uvicorn
apareciam no terminal — o que dava a impressão de que a aplicação não logava
nada, quando na verdade os logs existiam e estavam sendo jogados fora.

Configuramos o ROOT logger (e não só o namespace `imobly`) porque os módulos
usam `logging.getLogger(__name__)`, o que produz nomes como
`src.tenants.router` — um handler apenas em `imobly` deixaria a maior parte
do projeto muda.

Não há risco de log duplicado dos acessos HTTP: o uvicorn registra
`uvicorn`/`uvicorn.access` com `propagate = False`, então eles não sobem
para o root.
"""

import logging
import os
import sys

# Bibliotecas que falam demais em INFO. Cada requisição do httpx/supabase
# geraria uma linha, afogando os logs da aplicação.
_BIBLIOTECAS_SILENCIADAS = (
    "httpx",
    "httpcore",
    "hpack",
    "urllib3",
    "supabase",
    "gotrue",
    "storage3",
    "apscheduler.executors.default",
)


def configurar_logging(debug: bool = False) -> None:
    """
    Instala um handler de stdout no root logger.

    O nível vem de LOG_LEVEL; sem essa variável, INFO em modo debug e WARNING
    fora dele — para não vazar detalhe operacional em produção por acidente.
    """
    nivel_padrao = "INFO" if debug else "WARNING"
    nivel = os.getenv("LOG_LEVEL", nivel_padrao).strip().upper()

    root = logging.getLogger()

    # Idempotente: sem isso, um reload do uvicorn em dev empilharia handlers
    # e cada linha apareceria várias vezes.
    for handler in list(root.handlers):
        if getattr(handler, "_imobly", False):
            root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(levelname)-8s %(name)s: %(message)s"))
    handler._imobly = True  # type: ignore[attr-defined]

    root.addHandler(handler)
    root.setLevel(nivel)

    for nome in _BIBLIOTECAS_SILENCIADAS:
        logging.getLogger(nome).setLevel(logging.WARNING)
