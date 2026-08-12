"""remover colunas-lixo de contracts

`titulo` e `titulozin` duplicam `title`, nunca existiram no modelo SQLAlchemy
e nunca foram lidas ou escritas pela aplicação — resíduo de iteração
automatizada sobre o schema.

A remoção é feita depois de conferir que estão de fato vazias. Se houver
qualquer valor, a migration aborta: pode ser que alguém tenha passado a usar a
coluna por fora da aplicação, e nesse caso a decisão é do time, não desta
migration.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLUNAS = ("titulo", "titulozin")


def upgrade() -> None:
    conn = op.get_bind()

    for coluna in _COLUNAS:
        existe = conn.execute(
            sa.text(
                """
                SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'contracts' AND column_name = :coluna
                """
            ),
            {"coluna": coluna},
        ).scalar()

        if not existe:
            continue

        preenchidas = conn.execute(
            sa.text(f"SELECT count(*) FROM contracts WHERE {coluna} IS NOT NULL")
        ).scalar()

        if preenchidas:
            raise RuntimeError(
                f"contracts.{coluna} tem {preenchidas} linha(s) preenchida(s). "
                "Esperava-se coluna morta — confirme com o time antes de remover."
            )

        op.drop_column("contracts", coluna)


def downgrade() -> None:
    # Recria as colunas vazias; o conteúdo original era nulo por definição.
    for coluna in _COLUNAS:
        op.add_column("contracts", sa.Column(coluna, sa.String(), nullable=True))
