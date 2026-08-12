"""
Ambiente do Alembic.

Fonte da URL do banco (nesta ordem):
  1. ALEMBIC_DATABASE_URL  — use para apontar migrations à conexão DIRETA do
     Postgres (porta 5432). O pooler do Supabase (PgBouncer, porta 6543) opera
     em transaction pooling e não suporta com segurança DDL longo, advisory
     locks nem `CREATE INDEX CONCURRENTLY`.
  2. settings.DATABASE_URL — mesma resolução por ambiente usada pela aplicação.

O `target_metadata` agrega TODOS os modelos: qualquer módulo novo precisa ser
importado aqui, senão o autogenerate proporá dropar as tabelas dele.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.database import Base

# ── Importar todos os modelos para popular Base.metadata ──
# (a ordem não importa; os imports existem pelo efeito colateral de registro)
from src.auth.models import User  # noqa: F401
from src.contracts.models import Contract  # noqa: F401
from src.expenses.models import Expense  # noqa: F401
from src.notifications.models import Notification  # noqa: F401
from src.payments.models import Payment  # noqa: F401
from src.properties.models import Property  # noqa: F401
from src.tenants.models import Tenant  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    url = os.getenv("ALEMBIC_DATABASE_URL")
    if url:
        return url

    from src.config import settings

    if not settings.DATABASE_URL:
        raise RuntimeError(
            "Nenhuma URL de banco disponível. Defina ALEMBIC_DATABASE_URL "
            "(conexão direta, porta 5432) ou DATABASE_URL."
        )
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    """Gera o SQL sem conectar — útil para revisão do DDL antes de aplicar."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Aplica as migrations com uma conexão real."""
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            # Cada revisão em sua própria transação: uma falha no meio da fila
            # não desfaz as revisões já aplicadas com sucesso.
            transaction_per_migration=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
