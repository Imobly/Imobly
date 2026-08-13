"""impede dois contratos ativos sobrepostos no mesmo imóvel

Nada impedia dupla locação: nem o código, nem o banco. Dois cliques no botão
de salvar, ou duas requisições concorrentes, criavam contratos ativos
sobrepostos para o mesmo imóvel — e os pagamentos gerados a partir daí ficavam
ambíguos, sem como saber a qual locação pertencem.

Uma checagem em Python (SELECT antes do INSERT) não resolve: entre a consulta
e a gravação existe uma janela em que a outra requisição grava. A garantia
precisa estar no banco.

`EXCLUDE USING gist` é a ferramenta certa: rejeita qualquer par de linhas cujo
`property_id` seja igual E cujos períodos se sobreponham, considerando apenas
contratos ativos. Exige a extensão `btree_gist` para combinar igualdade
(integer) com sobreposição (intervalo) no mesmo índice.

O intervalo é `[]` (fechado nos dois lados) porque `end_date` é o último dia de
vigência, não o primeiro dia livre: um contrato terminando dia 31 e outro
começando dia 31 seriam sobreposição real.

ATENÇÃO: aborta se já houver sobreposições. Corrija-as antes — a constraint
não tem como adivinhar qual contrato é o correto.

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CONSTRAINT = "contratos_ativos_sem_sobreposicao"


def upgrade() -> None:
    conn = op.get_bind()

    sobreposicoes = conn.execute(
        sa.text(
            """
            SELECT a.id AS contrato_a, b.id AS contrato_b, a.property_id
              FROM contracts a
              JOIN contracts b
                ON a.property_id = b.property_id
               AND a.id < b.id
               AND a.status = 'ativo'
               AND b.status = 'ativo'
               AND daterange(a.start_date, a.end_date, '[]')
                && daterange(b.start_date, b.end_date, '[]')
             LIMIT 10
            """
        )
    ).fetchall()

    if sobreposicoes:
        raise RuntimeError(
            "Existem contratos ativos sobrepostos no mesmo imóvel; resolva antes "
            f"de aplicar esta migration.\n  pares conflitantes: {sobreposicoes}"
        )

    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        f"""
        ALTER TABLE contracts
          ADD CONSTRAINT {_CONSTRAINT}
          EXCLUDE USING gist (
            property_id WITH =,
            daterange(start_date, end_date, '[]') WITH &&
          ) WHERE (status = 'ativo')
        """
    )


def downgrade() -> None:
    op.execute(f"ALTER TABLE contracts DROP CONSTRAINT IF EXISTS {_CONSTRAINT}")
    # `btree_gist` não é removida: outros objetos podem depender dela.
