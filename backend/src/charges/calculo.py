"""
Posição financeira de uma cobrança: quanto é devido hoje, quanto entrou,
quanto falta.

A regra de ouro: multa e juros são FUNÇÃO DA DATA, não um valor gravado. Uma
dívida em aberto cresce todo dia, e o painel precisa mostrar o valor de hoje —
não o que foi calculado no dia em que alguém digitou o registro.

A data de referência dos encargos depende de a dívida estar quitada ou não:

  • quitada  → congela na data do recebimento que zerou o saldo. Depois que o
               inquilino pagou, a conta dele parou de correr.
  • em aberto → hoje. O saldo de amanhã é maior que o de hoje.

Os recebimentos são processados em ordem cronológica porque a decisão "este
recebimento quitou?" depende do total devido NAQUELE dia — e esse total é
diferente do de hoje.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable, Optional, Sequence

from src.core.tempo import hoje_brt
from .encargos import calcular_pagamento, dinheiro

# Situações possíveis de uma cobrança. `cancelada` não é calculada: é um estado
# administrativo e curto-circuita todo o resto.
ABERTA = "aberta"
PARCIAL = "parcial"
VENCIDA = "vencida"
QUITADA = "quitada"
CANCELADA = "cancelada"

STATUS_EM_ABERTO = (ABERTA, PARCIAL, VENCIDA)


@dataclass(frozen=True)
class Recebimento:
    """Projeção mínima de um `PaymentEntry` — mantém o cálculo testável sem ORM."""

    data: date
    valor: Decimal


@dataclass(frozen=True)
class PosicaoCobranca:
    base: Decimal            # aluguel + encargos - desconto
    multa: Decimal
    juros: Decimal
    total_devido: Decimal    # base + multa + juros na data de referência
    pago: Decimal            # soma dos recebimentos
    saldo: Decimal           # o que ainda falta; 0 quando quitada
    dias_atraso: int
    status: str
    referencia: date         # data usada para calcular multa e juros
    data_quitacao: Optional[date]

    @property
    def acrescimo(self) -> Decimal:
        return dinheiro(self.multa + self.juros)


def base_da_cobranca(rent_amount, charges_amount=0, discount_amount=0) -> Decimal:
    """
    Valor principal da cobrança, antes de qualquer encargo por atraso.

    O desconto entra aqui (e não depois da multa) de propósito: desconto de
    pontualidade incide sobre o aluguel, não sobre a penalidade.
    """
    return dinheiro(
        dinheiro(rent_amount) + dinheiro(charges_amount) - dinheiro(discount_amount)
    )


def calcular_posicao(
    *,
    rent_amount,
    charges_amount=0,
    discount_amount=0,
    fine_rate=0,
    interest_rate=0,
    due_date: date,
    recebimentos: Sequence[Recebimento] | Iterable[Recebimento] = (),
    status_armazenado: Optional[str] = None,
    hoje: Optional[date] = None,
) -> PosicaoCobranca:
    """
    Calcula a posição de UMA cobrança.

    `status_armazenado` só é consultado para respeitar o cancelamento — nenhum
    outro status vindo do banco influencia o resultado, senão a coluna
    derivada passaria a mandar no cálculo que deveria derivá-la.
    """
    hoje = hoje or hoje_brt()
    base = base_da_cobranca(rent_amount, charges_amount, discount_amount)

    entradas = sorted(recebimentos, key=lambda r: r.data)
    pago_total = dinheiro(sum((dinheiro(r.valor) for r in entradas), Decimal(0)))

    if status_armazenado == CANCELADA:
        return PosicaoCobranca(
            base=base,
            multa=Decimal("0.00"),
            juros=Decimal("0.00"),
            total_devido=Decimal("0.00"),
            pago=pago_total,
            saldo=Decimal("0.00"),
            dias_atraso=0,
            status=CANCELADA,
            referencia=hoje,
            data_quitacao=None,
        )

    # ── Houve quitação em algum recebimento? ──
    # Percorre em ordem: para cada recebimento, o devido é o daquela data.
    acumulado = Decimal(0)
    data_quitacao: Optional[date] = None
    for entrada in entradas:
        acumulado = dinheiro(acumulado + dinheiro(entrada.valor))
        devido_na_data = calcular_pagamento(
            aluguel=base,
            taxa_multa=fine_rate,
            taxa_juros=interest_rate,
            vencimento=due_date,
            data_pagamento=entrada.data,
        ).total_devido
        if acumulado >= devido_na_data:
            data_quitacao = entrada.data
            break

    referencia = data_quitacao or hoje

    calculo = calcular_pagamento(
        aluguel=base,
        taxa_multa=fine_rate,
        taxa_juros=interest_rate,
        vencimento=due_date,
        data_pagamento=referencia,
        valor_pago=pago_total,
    )

    if data_quitacao is not None:
        status = QUITADA
    elif pago_total > 0:
        # Continua `parcial` mesmo depois de vencer. O status antigo trocava
        # `parcial` por `atrasado` na virada do dia e apagava a informação de
        # que houve pagamento — justamente o caso que mais importa cobrar.
        status = PARCIAL
    elif calculo.dias_atraso > 0:
        status = VENCIDA
    else:
        status = ABERTA

    return PosicaoCobranca(
        base=base,
        multa=calculo.multa,
        juros=calculo.juros,
        total_devido=calculo.total_devido,
        pago=pago_total,
        saldo=calculo.restante,
        dias_atraso=calculo.dias_atraso,
        status=status,
        referencia=referencia,
        data_quitacao=data_quitacao,
    )


def posicao_de(charge, recebimentos: Sequence[Recebimento], hoje: Optional[date] = None) -> PosicaoCobranca:
    """Atalho para calcular a posição direto de uma instância `Charge`."""
    return calcular_posicao(
        rent_amount=charge.rent_amount,
        charges_amount=charge.charges_amount,
        discount_amount=charge.discount_amount,
        fine_rate=charge.fine_rate,
        interest_rate=charge.interest_rate,
        due_date=charge.due_date,
        recebimentos=recebimentos,
        status_armazenado=charge.status,
        hoje=hoje,
    )


# ── Faixas de aging ──────────────────────────────────────────────────────────
# Os cortes são os do relatório padrão de inadimplência do mercado. Mudá-los
# muda o significado de todos os números do painel: altere aqui, num lugar só.
FAIXAS_AGING = (
    ("a_vencer", None, 0),
    ("d1_30", 1, 30),
    ("d31_60", 31, 60),
    ("d61_90", 61, 90),
    ("d90_mais", 91, None),
)


def faixa_aging(dias_atraso: int) -> str:
    """Classifica um atraso em dias na faixa de aging correspondente."""
    if dias_atraso <= 0:
        return "a_vencer"
    if dias_atraso <= 30:
        return "d1_30"
    if dias_atraso <= 60:
        return "d31_60"
    if dias_atraso <= 90:
        return "d61_90"
    return "d90_mais"


# ── Situação do inquilino ────────────────────────────────────────────────────
# Derivada do PIOR atraso em aberto, não da média: um inquilino com uma dívida
# de 90 dias e três cobranças em dia é um problema de 90 dias.

def situacao_inquilino(dias_atraso_maximo: int, saldo_total: Decimal) -> str:
    if saldo_total <= 0 or dias_atraso_maximo <= 0:
        return "em_dia"
    if dias_atraso_maximo <= 15:
        return "atraso_leve"
    if dias_atraso_maximo <= 60:
        return "inadimplente"
    return "critico"
