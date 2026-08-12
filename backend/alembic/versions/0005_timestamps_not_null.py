"""timestamps NOT NULL com default no banco

`created_at`/`updated_at` eram nullable e SEM default em contracts, payments,
properties, tenants, expenses e notifications — mas os response models
(`PropertyRead`, `PaymentRead`, ...) declaram `datetime` não-opcional.

Consequência: qualquer linha inserida fora do ORM (seed, importação, correção
manual em SQL) fazia a listagem INTEIRA responder 500 — um único registro com
timestamp nulo derrubava `GET /properties` para todos os imóveis do usuário.

Esta revisão preenche os nulos existentes, aplica DEFAULT now() e exige
NOT NULL, passando a responsabilidade do preenchimento para o banco.

Sobre fuso: as colunas continuam `timestamp without time zone`. A aplicação
grava `datetime.utcnow()` (UTC ingênuo), então converter para `timestamptz`
agora exigiria afirmar o fuso dos dados históricos. Fica registrado como
dívida (achado M-07) para ser feito junto da unificação de fuso na aplicação,
com uma migration dedicada e explícita:
    ALTER TABLE x ALTER COLUMN created_at TYPE timestamptz
        USING created_at AT TIME ZONE 'UTC';

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# notifications entra junto: o modelo declara os timestamps NOT NULL com
# server_default, mas o banco os criou nullable.
_TABELAS = ("contracts", "payments", "properties", "tenants", "expenses", "notifications")


def upgrade() -> None:
    for tabela in _TABELAS:
        # Preenche o que já está nulo. `updated_at` herda `created_at` quando
        # possível, para não inventar uma data de modificação mais recente que
        # a realidade.
        op.execute(f"UPDATE {tabela} SET created_at = now() WHERE created_at IS NULL")
        op.execute(
            f"UPDATE {tabela} SET updated_at = COALESCE(created_at, now()) "
            f"WHERE updated_at IS NULL"
        )

        for coluna in ("created_at", "updated_at"):
            op.alter_column(
                tabela,
                coluna,
                existing_type=sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            )


def downgrade() -> None:
    for tabela in _TABELAS:
        for coluna in ("created_at", "updated_at"):
            op.alter_column(
                tabela,
                coluna,
                existing_type=sa.DateTime(),
                nullable=True,
                server_default=None,
            )
