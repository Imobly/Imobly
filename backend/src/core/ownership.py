"""
Validação de posse de entidades referenciadas (guarda anti-IDOR).

Todo endpoint já força `user_id` a partir do token, mas as chaves estrangeiras
(`property_id`, `tenant_id`, `contract_id`) chegavam cruas do payload e eram
gravadas sem verificação. Isso permitia criar um contrato/pagamento/despesa
apontando para o imóvel ou o inquilino de OUTRO usuário — e, via os JOINs do
dashboard, ler o nome dessas entidades alheias.

Regra: nenhuma FK vinda do cliente é gravada sem passar por aqui.

O 404 (em vez de 403) é deliberado: responder "não encontrado" para o que
existe mas pertence a terceiros evita confirmar a existência do registro —
caso contrário o próprio código de status vira um oráculo de enumeração.
"""

from __future__ import annotations

from typing import Optional, Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

T = TypeVar("T")

# Rótulos em português para as mensagens de erro
_LABELS: dict[str, str] = {
    "Property": "Imóvel",
    "Tenant": "Inquilino",
    "Contract": "Contrato",
    "Payment": "Pagamento",
    "Expense": "Despesa",
}


def assert_owned(db: Session, model: Type[T], obj_id, user_id: int) -> T:
    """
    Garante que `obj_id` existe E pertence a `user_id`; devolve a instância.

    Raises:
        HTTPException 404: se não existe ou é de outro usuário.
    """
    obj = (
        db.query(model)
        .filter(model.id == obj_id, model.user_id == user_id)
        .first()
    )
    if obj is None:
        label = _LABELS.get(model.__name__, model.__name__)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{label} não encontrado",
        )
    return obj


def assert_owned_optional(
    db: Session, model: Type[T], obj_id: Optional[int], user_id: int
) -> Optional[T]:
    """
    Igual a `assert_owned`, mas aceita `None` (campo opcional não informado).

    Cuidado: `None` significa "não mexer neste vínculo" e passa direto; qualquer
    valor informado é validado.
    """
    if obj_id is None:
        return None
    return assert_owned(db, model, obj_id, user_id)
