"""colunas obrigatórias no schema Pydantic passam a ser NOT NULL no banco

Mesma família de defeito da revisão 0005 (timestamps), encontrada ao testar a
listagem após uma inserção em SQL puro:

    properties.parking_spaces  nullable no banco  ×  `int` obrigatório no schema
    properties.status          nullable           ×  `str` obrigatório
    contracts.rent             nullable           ×  `Decimal` obrigatório
    contracts.status           nullable           ×  `str` obrigatório
    payments.fine_amount       nullable           ×  `Decimal` obrigatório

Os defaults existiam apenas no lado Python (`Column(..., default=0)`), que só
atua em inserts feitos pelo ORM. Qualquer seed, importação ou correção manual
em SQL gravava NULL, e o response model quebrava a listagem INTEIRA com 500 —
um único registro derrubava a página para todos os outros.

Passando o default para o banco, a garantia vale para qualquer caminho de
escrita.

`contracts.rent` não recebe default: aluguel é dado de negócio e inventar
zero seria pior que falhar. Linhas existentes com rent nulo são preenchidas
com 0 apenas para viabilizar o NOT NULL — a migration avisa se encontrar
alguma, para que o time corrija o valor real.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (tabela, coluna, tipo, default_sql)
_COLUNAS = [
    ("properties", "parking_spaces", sa.Integer(), "0"),
    ("properties", "status", sa.String(), "'vacant'"),
    ("contracts", "status", sa.String(), "'ativo'"),
    ("payments", "fine_amount", sa.Numeric(), "0"),
]


def upgrade() -> None:
    conn = op.get_bind()

    for tabela, coluna, tipo, default in _COLUNAS:
        op.execute(f"UPDATE {tabela} SET {coluna} = {default} WHERE {coluna} IS NULL")
        op.alter_column(
            tabela,
            coluna,
            existing_type=tipo,
            nullable=False,
            server_default=sa.text(default),
        )

    # contracts.rent — sem default; apenas sinaliza se houver dados a corrigir.
    nulos = conn.execute(sa.text("SELECT count(*) FROM contracts WHERE rent IS NULL")).scalar()
    if nulos:
        print(
            f"AVISO: {nulos} contrato(s) com `rent` nulo foram preenchidos com 0 "
            "para permitir NOT NULL. Corrija os valores reais."
        )
        op.execute("UPDATE contracts SET rent = 0 WHERE rent IS NULL")

    op.alter_column("contracts", "rent", existing_type=sa.Numeric(), nullable=False)


def downgrade() -> None:
    op.alter_column("contracts", "rent", existing_type=sa.Numeric(), nullable=True)

    for tabela, coluna, tipo, _default in _COLUNAS:
        op.alter_column(
            tabela,
            coluna,
            existing_type=tipo,
            nullable=True,
            server_default=None,
        )
