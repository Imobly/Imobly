"""
Referência única de data e hora da aplicação.

O código misturava `date.today()` (fuso do processo — UTC no container) com
`datetime.now(BRT)`. As duas convivendo produziam incoerência visível: entre
21h e meia-noite no horário de Brasília, `date.today()` já apontava para o dia
seguinte em UTC, e dois endpoints do MESMO dashboard reportavam meses
diferentes na virada — a receita "sumia" da tela.

O negócio é brasileiro: a data de referência é a de São Paulo. Todo lugar que
precisa de "hoje" deve usar `hoje_brt()`.
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

BRT = ZoneInfo("America/Sao_Paulo")


def agora_brt() -> datetime:
    """Instante atual no fuso de São Paulo (timezone-aware)."""
    return datetime.now(BRT)


def hoje_brt() -> date:
    """
    Data de hoje no fuso de São Paulo.

    Use em vez de `date.today()`, que devolve a data do fuso do processo —
    UTC nos containers, o que adianta a virada do dia em 3 horas.
    """
    return agora_brt().date()
