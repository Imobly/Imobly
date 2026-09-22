"""
Módulo de pagamentos — rotas de compatibilidade sobre `charges`.

`PaymentRepository` não existe mais: a tabela `payments` deixou de receber
escrita na revisão 0012. Quem precisa gravar dinheiro usa `ChargeRepository`.
"""

from .router import router
from .schema import PaymentCreate, PaymentResponse, PaymentUpdate
from .models import Payment

__all__ = ["router", "PaymentCreate", "PaymentResponse", "PaymentUpdate", "Payment"]
