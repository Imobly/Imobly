"""
Cálculo de multa, juros e situação de um pagamento.

Extraído de `router.py`, onde estava duplicado entre `/calculate` e
`/register` — duas cópias que já divergiam (só `/register` gravava, e o
arredondamento diferia).

Tudo em `Decimal`. O código anterior convertia para `float`, o que em dinheiro
não é detalhe de arredondamento e sim defeito contábil: `2500.00 * 1.02`
resulta em `2550.0000000000005` em ponto flutuante binário, então um pagamento
exato caía em `paid >= total_expected` como False e era classificado como
"parcial" — gerando cobrança indevida de multa e registro falso de
inadimplência.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from src.core.tempo import hoje_brt

CENTAVO = Decimal("0.01")
DIAS_DO_MES = Decimal(30)


def dinheiro(valor) -> Decimal:
    """Normaliza para duas casas, arredondando como se espera em dinheiro."""
    return Decimal(str(valor or 0)).quantize(CENTAVO, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class ResultadoCalculo:
    base: Decimal
    multa: Decimal
    juros: Decimal
    total_devido: Decimal
    pago: Decimal
    restante: Decimal
    dias_atraso: int
    situacao: str

    @property
    def acrescimo(self) -> Decimal:
        return dinheiro(self.multa + self.juros)


def calcular_pagamento(
    *,
    aluguel,
    taxa_multa,
    taxa_juros,
    vencimento: date,
    data_pagamento: date | None,
    valor_pago=None,
) -> ResultadoCalculo:
    """
    Calcula multa, juros e a situação resultante do pagamento.

    - Multa: percentual fixo sobre o aluguel, aplicado uma vez, se houver atraso.
    - Juros: percentual ao mês, proporcional aos dias de atraso.

    `data_pagamento` nula significa "hoje" — usada pela simulação, em que o
    pagamento ainda não ocorreu.
    """
    base = dinheiro(aluguel)
    multa_pct = dinheiro(taxa_multa)
    juros_pct = dinheiro(taxa_juros)
    pago = dinheiro(valor_pago)

    referencia = data_pagamento or hoje_brt()
    dias_atraso = max(0, (referencia - vencimento).days)

    multa = Decimal(0)
    juros = Decimal(0)
    if dias_atraso > 0:
        multa = dinheiro(base * multa_pct / 100)
        juros = dinheiro(base * (juros_pct / 100) * (Decimal(dias_atraso) / DIAS_DO_MES))

    total_devido = dinheiro(base + multa + juros)
    restante = dinheiro(max(Decimal(0), total_devido - pago))

    # A ordem importa: "pago" exige quitação integral; qualquer valor menor que
    # o devido é parcial, mesmo que o atraso também se aplique.
    if pago >= total_devido and pago > 0:
        situacao = "pago"
    elif pago > 0:
        situacao = "parcial"
    elif dias_atraso > 0:
        situacao = "atrasado"
    else:
        situacao = "pendente"

    return ResultadoCalculo(
        base=base,
        multa=multa,
        juros=juros,
        total_devido=total_devido,
        pago=pago,
        restante=restante,
        dias_atraso=dias_atraso,
        situacao=situacao,
    )
