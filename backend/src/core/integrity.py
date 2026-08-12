"""
Tradução de violações de integridade do Postgres em respostas HTTP corretas.

Depois que as políticas ON DELETE passaram a existir de fato no banco
(revisão 0006), tentar apagar um registro ainda referenciado levanta
`IntegrityError`. Sem tratamento isso vira 500 — que sugere defeito do
servidor, quando na verdade é uma regra de negócio: "não dá para apagar este
inquilino porque ele tem contrato".

`foreign_key_violation` → 409 Conflict com mensagem acionável.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# SQLSTATE do Postgres
_FOREIGN_KEY_VIOLATION = "23503"
_UNIQUE_VIOLATION = "23505"


def _sqlstate(exc: IntegrityError) -> str | None:
    return getattr(getattr(exc, "orig", None), "pgcode", None)


@contextmanager
def traduzir_erros_de_integridade(
    db: Session,
    *,
    conflito_fk: str = "Registro não pode ser removido: existem dados vinculados a ele",
    conflito_unico: str = "Já existe um registro com estes dados",
):
    """
    Converte `IntegrityError` em `HTTPException` com o status adequado.

    Faz rollback antes de levantar: a sessão fica inutilizável após um erro de
    integridade, e sem isso a próxima operação na mesma requisição falharia com
    um erro sem relação com a causa.
    """
    try:
        yield
    except IntegrityError as exc:
        db.rollback()
        codigo = _sqlstate(exc)

        if codigo == _FOREIGN_KEY_VIOLATION:
            logger.info("Violação de FK traduzida para 409: %s", exc.orig)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflito_fk)

        if codigo == _UNIQUE_VIOLATION:
            logger.info("Violação de unicidade traduzida para 409: %s", exc.orig)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflito_unico)

        # Qualquer outra violação é defeito de verdade — deixe estourar como 500
        # para não mascarar um problema real atrás de um 4xx.
        logger.exception("Erro de integridade não previsto")
        raise
