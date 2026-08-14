"""unicidade de inquilinos por locador, não global

`tenants.email` e `tenants.cpf_cnpj` eram UNIQUE globais, mas a aplicação
verifica duplicidade filtrando por `user_id`. Duas consequências:

  1. Funcional: dois locadores não conseguiam cadastrar o MESMO inquilino —
     cenário corriqueiro no domínio. A checagem da aplicação passava e o
     INSERT estourava com 500 (IntegrityError).
  2. Vazamento por canal lateral: o 500 confirmava que aquele CPF/e-mail já
     existia na base de outro cliente — enumeração de inquilinos alheios.

A unicidade correta é composta: (user_id, email) e (user_id, cpf_cnpj).

O e-mail passa a ser único por `lower(email)` para que "A@x.com" e "a@x.com"
não convivam no mesmo locador.

ATENÇÃO: se já existirem duplicatas dentro de um mesmo user_id, a criação dos
índices falha. A migration detecta esse caso e aborta com uma mensagem
explícita, em vez de deixar o banco num estado ambíguo.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _abort_se_houver_duplicatas() -> None:
    """Falha cedo e com diagnóstico, em vez de deixar o CREATE INDEX estourar."""
    conn = op.get_bind()

    dup_email = conn.execute(
        sa.text(
            """
            SELECT user_id, lower(email) AS chave, count(*) AS n
              FROM tenants
             GROUP BY user_id, lower(email)
            HAVING count(*) > 1
             LIMIT 5
            """
        )
    ).fetchall()

    dup_cpf = conn.execute(
        sa.text(
            """
            SELECT user_id, cpf_cnpj AS chave, count(*) AS n
              FROM tenants
             GROUP BY user_id, cpf_cnpj
            HAVING count(*) > 1
             LIMIT 5
            """
        )
    ).fetchall()

    if dup_email or dup_cpf:
        raise RuntimeError(
            "Existem inquilinos duplicados dentro do mesmo locador; resolva antes "
            f"de aplicar esta migration.\n  e-mails duplicados: {dup_email}\n"
            f"  CPF/CNPJ duplicados: {dup_cpf}"
        )


def upgrade() -> None:
    _abort_se_houver_duplicatas()

    conn = op.get_bind()

    # Remove as constraints globais (IF EXISTS: o nome pode divergir em bancos
    # cujo schema foi criado fora do Alembic).
    op.execute("ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_email_key")
    op.execute("ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_cpf_cnpj_key")

    # Unicidade composta, por locador
    op.create_index(
        "ux_tenants_user_email",
        "tenants",
        ["user_id", sa.text("lower(email)")],
        unique=True,
    )
    op.create_index(
        "ux_tenants_user_cpf",
        "tenants",
        ["user_id", "cpf_cnpj"],
        unique=True,
    )

    # Consultas de listagem sempre filtram por dono. O índice pode já existir
    # no banco (criado fora do Alembic) — checar evita quebrar a migration.
    ja_existe = conn.execute(
        sa.text(
            "SELECT 1 FROM pg_indexes "
            "WHERE schemaname='public' AND indexname='ix_tenants_user_id'"
        )
    ).scalar()
    if not ja_existe:
        op.create_index("ix_tenants_user_id", "tenants", ["user_id"])


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tenants_user_id")
    op.drop_index("ux_tenants_user_cpf", table_name="tenants")
    op.drop_index("ux_tenants_user_email", table_name="tenants")
    op.create_unique_constraint("tenants_cpf_cnpj_key", "tenants", ["cpf_cnpj"])
    op.create_unique_constraint("tenants_email_key", "tenants", ["email"])
