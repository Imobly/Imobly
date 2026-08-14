"""alinhar a tabela notifications aos modelos (módulo estava inoperante)

O modelo SQLAlchemy e o banco divergiram a ponto de endpoints de notificações
responderem 500 por colunas ausentes.

Esta revisão é DEFENSIVA: inspeciona o schema antes de cada operação. O motivo
é concreto — o `DDL.sql` do repositório descrevia `notifications` com
`is_read`, `link` e `metadata`, mas o banco real já tinha `read_status`,
`priority`, `date`, `action_required`, `related_id` e `related_type`, e NÃO
tinha `link` nem `metadata`. Uma migration escrita contra o DDL falharia no
primeiro `RENAME`.

Bancos criados do zero (a partir da revisão 0001) e o banco existente
convergem para o mesmo estado final.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELA = "notifications"


def _colunas() -> set:
    conn = op.get_bind()
    return {
        linha[0]
        for linha in conn.execute(
            sa.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=:t"
            ),
            {"t": TABELA},
        )
    }


def _indices() -> set:
    conn = op.get_bind()
    return {
        linha[0]
        for linha in conn.execute(
            sa.text("SELECT indexname FROM pg_indexes WHERE schemaname='public'")
        )
    }


def upgrade() -> None:
    cols = _colunas()

    # ── is_read → read_status (só se o banco ainda usar o nome antigo) ──
    if "is_read" in cols and "read_status" not in cols:
        op.alter_column(TABELA, "is_read", new_column_name="read_status")
        cols = _colunas()

    if "read_status" in cols:
        op.execute(f"UPDATE {TABELA} SET read_status = false WHERE read_status IS NULL")
        op.alter_column(
            TABELA,
            "read_status",
            existing_type=sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        )

    # ── Colunas que o modelo espera; adiciona só o que faltar ──
    faltantes = [
        ("priority", sa.Column("priority", sa.String(20), nullable=False,
                               server_default="medium")),
        ("date", sa.Column("date", sa.Date(), nullable=False,
                           server_default=sa.text("CURRENT_DATE"))),
        ("action_required", sa.Column("action_required", sa.Boolean(), nullable=False,
                                      server_default=sa.text("false"))),
        ("related_id", sa.Column("related_id", sa.String(50), nullable=True)),
        ("related_type", sa.Column("related_type", sa.String(50), nullable=True)),
        # `link` e `metadata` faltavam no banco real, embora o DDL os descrevesse.
        ("link", sa.Column("link", sa.Text(), nullable=True)),
        ("metadata", sa.Column("metadata", sa.JSON(), nullable=True)),
    ]
    for nome, coluna in faltantes:
        if nome not in cols:
            op.add_column(TABELA, coluna)

    # ── FK para users: ausente no banco real ──
    conn = op.get_bind()
    tem_fk = conn.execute(
        sa.text(
            "SELECT 1 FROM pg_constraint "
            "WHERE conrelid='public.notifications'::regclass AND contype='f'"
        )
    ).scalar()
    if not tem_fk:
        # Remove órfãs antes de criar a FK, senão a criação falha.
        op.execute(
            f"DELETE FROM {TABELA} WHERE user_id NOT IN (SELECT id FROM users)"
        )
        op.create_foreign_key(
            "notifications_user_id_fkey",
            TABELA, "users", ["user_id"], ["id"],
            ondelete="CASCADE",
        )

    # `has_recent_notification` (antispam) filtra por estas colunas.
    if "ix_notifications_antispam" not in _indices():
        op.create_index(
            "ix_notifications_antispam",
            TABELA,
            ["user_id", "related_id", "type", "created_at"],
        )
    if "ix_notifications_user_id" not in _indices():
        op.create_index("ix_notifications_user_id", TABELA, ["user_id"])


def downgrade() -> None:
    for indice in ("ix_notifications_antispam",):
        if indice in _indices():
            op.drop_index(indice, table_name=TABELA)

    cols = _colunas()
    for coluna in ("related_type", "related_id", "action_required", "date", "priority"):
        if coluna in cols:
            op.drop_column(TABELA, coluna)

    if "read_status" in cols:
        op.alter_column(
            TABELA, "read_status",
            existing_type=sa.Boolean(), nullable=True, server_default=None,
        )
        op.alter_column(TABELA, "read_status", new_column_name="is_read")
