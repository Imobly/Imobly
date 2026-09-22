"""
Compatibilidade — o cálculo agora vive em `src/charges/encargos.py`.

Multa e juros são regra da cobrança, não do registro de pagamento, e manter a
implementação aqui criava um ciclo de imports entre `payments` e `charges`.
Este módulo existe só para não quebrar quem já importava daqui.
"""

from src.charges.encargos import (  # noqa: F401
    CENTAVO,
    DIAS_DO_MES,
    ResultadoCalculo,
    calcular_pagamento,
    dinheiro,
)

__all__ = [
    "CENTAVO",
    "DIAS_DO_MES",
    "ResultadoCalculo",
    "calcular_pagamento",
    "dinheiro",
]
