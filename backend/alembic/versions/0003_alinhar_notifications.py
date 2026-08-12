"""alinhar a tabela notifications aos modelos (módulo estava inoperante)

O modelo SQLAlchemy e o banco divergiram a ponto de TODO endpoint de
notificações responder 500: o repositório consulta `read_status` e
`related_id`, colunas que não existiam no banco (`ProgrammingError: column
notifications.read_status does not exist`).

Divergências corrigidas aqui:
  • is_read            → read_status (NOT NULL, default false)
  • priority           → coluna nova (NOT NULL, default 'medium')
  • date               → coluna nova (NOT NULL, default CURRENT_DATE)
  • action_required    → coluna nova (NOT NULL, default false)
  • related_id/_type   → colunas novas (nullable)

A chave primária permanece `varchar(36)`: o modelo é que foi ajustado para
String(36) + uuid4, seguindo o padrão que `expenses` já usa. Converter a PK
para inteiro seria cirurgia arriscada sem benefício — nenhuma FK aponta para
notifications, e `NotificationResponse` já expõe o id como string.

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


def upgrade() -> None:
    # ── is_read → read_status ──
    op.alter_column("notifications", "is_read", new_column_name="read_status")
    # A coluna era nullable; normalize antes de exigir NOT NULL.
    op.execute("UPDATE notifications SET read_status = false WHERE read_status IS NULL")
    op.alter_column(
        "notifications",
        "read_status",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.text("false"),
    )

    # ── Colunas que o modelo espera e o banco não tinha ──
    op.add_column(
        "notifications",
        sa.Column(
            "priority",
            sa.String(length=20),
            nullable=False,
            server_default="medium",
        ),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "date",
            sa.Date(),
            nullable=False,
            server_default=sa.text("CURRENT_DATE"),
        ),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "action_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column("notifications", sa.Column("related_id", sa.String(length=50), nullable=True))
    op.add_column("notifications", sa.Column("related_type", sa.String(length=50), nullable=True))

    # `has_recent_notification` (lógica antispam) filtra por estas três colunas.
    op.create_index(
        "ix_notifications_antispam",
        "notifications",
        ["user_id", "related_id", "type", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_antispam", table_name="notifications")
    op.drop_column("notifications", "related_type")
    op.drop_column("notifications", "related_id")
    op.drop_column("notifications", "action_required")
    op.drop_column("notifications", "date")
    op.drop_column("notifications", "priority")
    op.alter_column(
        "notifications",
        "read_status",
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=None,
    )
    op.alter_column("notifications", "read_status", new_column_name="is_read")
