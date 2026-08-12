"""identidade de usuário por supabase_uid (imutável) em vez de e-mail

A identidade local era resolvida por `users.email`, e `PUT /auth/me` permitia
trocar esse e-mail livremente — sem verificar posse do novo endereço e sem
sincronizar com o Supabase. Uma chave de identidade mutável permite que um
usuário passe a resolver para o registro de outro.

Esta revisão adiciona `supabase_uid` (UUID do Supabase, imutável) e faz o
backfill a partir de `hashed_password`, que hoje armazena exatamente esse UUID
(ver `security.get_current_user_local_id`).

A coluna fica NULLABLE de propósito: linhas legadas cujo `hashed_password` não
seja um UUID válido não podem ser preenchidas aqui. A aplicação reivindica o
uid dessas linhas no primeiro login autenticado do respectivo usuário. Depois
que a telemetria mostrar zero linhas nulas, promova a NOT NULL numa revisão
posterior.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("supabase_uid", postgresql.UUID(as_uuid=False), nullable=True),
    )

    # Backfill: hashed_password guarda o UUID do Supabase. O regex evita que a
    # migration exploda em linhas com conteúdo inesperado.
    op.execute(
        """
        UPDATE users
           SET supabase_uid = hashed_password::uuid
         WHERE supabase_uid IS NULL
           AND hashed_password ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        """
    )

    op.create_index(
        "ix_users_supabase_uid",
        "users",
        ["supabase_uid"],
        unique=True,
        postgresql_where=sa.text("supabase_uid IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_users_supabase_uid", table_name="users")
    op.drop_column("users", "supabase_uid")
