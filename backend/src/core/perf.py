"""
Medidor de tempo por requisição ([PERF]).

Responde à pergunta "onde foi parar o tempo desta requisição?" sem precisar de
APM externo. O rastreador vive num ContextVar, então `marcar()` pode ser
chamado de qualquer camada (router, repository, service) sem ter que passar o
objeto `Request` adiante.

Desligado por padrão: só liga com PERF_PROFILING=true no ambiente. Quando
desligado, `marcar()` é um retorno imediato e o middleware nem entra no
caminho da requisição — custo zero em produção.

Uso:

    from src.core.perf import marcar

    @router.post("/")
    def create_tenant(...):
        marcar("validação de dados concluída")
        ...
        marcar("resposta do Supabase")

Saída no terminal:

    [PERF] POST /api/v1/tenants/ — início da requisição: 0ms
    [PERF]   validação de dados concluída: +15ms (15ms)
    [PERF]   resposta do Supabase: +450ms (465ms)
    [PERF] POST /api/v1/tenants/ — total da rota: 465ms (status 201)
"""

import logging
import os
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

logger = logging.getLogger("imobly.perf")

# Lido uma vez, na importação: alternar isso em runtime não faz sentido e
# a checagem entra no caminho quente de toda requisição.
PERF_ATIVO: bool = os.getenv("PERF_PROFILING", "false").strip().lower() in {
    "1", "true", "yes", "on",
}

# Requisições abaixo deste tempo total não são logadas quando
# PERF_APENAS_LENTAS=true — útil para achar outliers sem afogar o terminal.
_APENAS_LENTAS: bool = os.getenv("PERF_APENAS_LENTAS", "false").strip().lower() in {
    "1", "true", "yes", "on",
}
_LIMITE_LENTA_MS: float = float(os.getenv("PERF_LIMITE_MS", "500"))


@dataclass
class RastreadorDeTempo:
    """Acumula os marcos de uma requisição. Um por requisição."""

    rotulo: str
    inicio: float = field(default_factory=time.perf_counter)
    # (nome da etapa, ms desde o marco anterior, ms desde o início)
    marcos: List[Tuple[str, float, float]] = field(default_factory=list)
    _ultimo: Optional[float] = None

    def __post_init__(self) -> None:
        self._ultimo = self.inicio

    def marcar(self, etapa: str) -> None:
        agora = time.perf_counter()
        delta_ms = (agora - (self._ultimo or self.inicio)) * 1000
        total_ms = (agora - self.inicio) * 1000
        self.marcos.append((etapa, delta_ms, total_ms))
        self._ultimo = agora

    @property
    def total_ms(self) -> float:
        return (time.perf_counter() - self.inicio) * 1000

    def emitir(self, status_code: int) -> None:
        total = self.total_ms

        if _APENAS_LENTAS and total < _LIMITE_LENTA_MS:
            return

        # Uma linha por marco, para o terminal ficar legível na ordem em que
        # as etapas aconteceram.
        logger.info("[PERF] %s — início da requisição: 0ms", self.rotulo)
        for etapa, delta_ms, acumulado_ms in self.marcos:
            logger.info(
                "[PERF]   %s: +%.0fms (%.0fms)", etapa, delta_ms, acumulado_ms
            )
        logger.info(
            "[PERF] %s — total da rota: %.0fms (status %s)",
            self.rotulo, total, status_code,
        )


_rastreador_atual: ContextVar[Optional[RastreadorDeTempo]] = ContextVar(
    "rastreador_de_tempo", default=None
)


def marcar(etapa: str) -> None:
    """
    Registra um marco na requisição em andamento.

    Silencioso e barato quando o profiling está desligado ou quando chamado
    fora de uma requisição (scheduler, script, teste) — nunca levanta.
    """
    if not PERF_ATIVO:
        return
    rastreador = _rastreador_atual.get()
    if rastreador is not None:
        rastreador.marcar(etapa)


def rastreador_atual() -> Optional[RastreadorDeTempo]:
    """Acesso direto ao rastreador, para casos que precisam do total parcial."""
    return _rastreador_atual.get()


async def middleware_de_perf(request, call_next):
    """
    Middleware HTTP que cria o rastreador e emite o relatório ao final.

    Registrado em `main.py` apenas quando PERF_ATIVO, para não adicionar um
    frame na pilha de middlewares em produção.
    """
    rastreador = RastreadorDeTempo(
        rotulo=f"{request.method} {request.url.path}"
    )
    token = _rastreador_atual.set(rastreador)
    # Também no request.state: acessível de dependências que já recebem Request.
    request.state.perf = rastreador

    status_code = 500
    try:
        resposta = await call_next(request)
        status_code = resposta.status_code
        return resposta
    finally:
        # `finally` para que uma exceção ainda produza o relatório — uma rota
        # que estoura depois de 3s é justamente a que queremos medir.
        try:
            rastreador.emitir(status_code)
        finally:
            _rastreador_atual.reset(token)
