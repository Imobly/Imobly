"""baseline — retrato fiel do schema em produção

Esta revisão descreve o banco **como ele está hoje**, defeitos inclusive
(colunas-lixo em contracts, timestamps nullable, FKs sem ON DELETE,
notifications divergente dos modelos). Ela NÃO corrige nada — as correções
vêm nas revisões seguintes.

Por que assim: o baseline precisa ser um ponto comum entre o banco existente
e um banco criado do zero. Se ele já viesse corrigido, `alembic stamp 0001`
em produção marcaria como aplicadas correções que nunca rodaram.

  • Banco existente:  alembic stamp 0001   (não executa DDL)
  • Banco novo:       alembic upgrade head (executa tudo)

Revision ID: 0001
Revises:
Create Date: 2026-08-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="users_pkey"),
        sa.UniqueConstraint("email", name="users_email_key"),
    )

    # ── properties (FK para tenants adicionada depois — ciclo) ──
    op.create_table(
        "properties",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("neighborhood", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("zip_code", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("area", sa.Numeric(), nullable=False),
        sa.Column("bedrooms", sa.Integer(), nullable=False),
        sa.Column("bathrooms", sa.Integer(), nullable=False),
        sa.Column("parking_spaces", sa.Integer(), nullable=True),
        sa.Column("rent", sa.Numeric(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("images", sa.JSON(), nullable=True),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="properties_pkey"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="properties_user_id_fkey"),
    )

    # ── tenants (FK para contracts adicionada depois — ciclo) ──
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("cpf_cnpj", sa.String(), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("profession", sa.String(), nullable=False),
        sa.Column("emergency_contact", sa.JSON(), nullable=True),
        sa.Column("documents", sa.JSON(), nullable=True),
        sa.Column("contract_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="tenants_pkey"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="tenants_user_id_fkey"),
        # UNIQUE global (defeito conhecido — corrigido na revisão 0004)
        sa.UniqueConstraint("email", name="tenants_email_key"),
        sa.UniqueConstraint("cpf_cnpj", name="tenants_cpf_cnpj_key"),
    )

    # ── contracts ──
    op.create_table(
        "contracts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("rent", sa.Numeric(), nullable=True),
        sa.Column("deposit", sa.Numeric(), nullable=False),
        sa.Column("interest_rate", sa.Numeric(), nullable=False),
        sa.Column("fine_rate", sa.Numeric(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        # due_day veio de migrations/update_status_enum.sql
        sa.Column("due_day", sa.Integer(), nullable=True),
        # Colunas-lixo herdadas (removidas na revisão 0007)
        sa.Column("titulo", sa.String(), nullable=True),
        sa.Column("titulozin", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="contracts_pkey"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="contracts_user_id_fkey"),
        sa.ForeignKeyConstraint(
            ["property_id"], ["properties.id"], name="fk_contract_property_id"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_contract_tenant_id"),
    )

    # ── FKs que fecham o ciclo properties ↔ tenants ↔ contracts ──
    op.create_foreign_key(
        "fk_property_tenant_id", "properties", "tenants", ["tenant_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_tenant_contract_id", "tenants", "contracts", ["contract_id"], ["id"]
    )

    # ── payments ──
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("contract_id", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("amount", sa.Numeric(), nullable=False),
        sa.Column("fine_amount", sa.Numeric(), nullable=True),
        sa.Column("total_amount", sa.Numeric(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("payment_method", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="payments_pkey"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="payments_user_id_fkey"),
        sa.ForeignKeyConstraint(
            ["property_id"], ["properties.id"], name="payments_property_id_fkey"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="payments_tenant_id_fkey"),
        sa.ForeignKeyConstraint(
            ["contract_id"], ["contracts.id"], name="payments_contract_id_fkey"
        ),
    )

    # ── expenses ──
    op.create_table(
        "expenses",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=True),
        sa.Column("vendor", sa.String(), nullable=True),
        sa.Column("number", sa.String(), nullable=True),
        sa.Column("receipt", sa.Text(), nullable=True),
        sa.Column("documents", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="expenses_pkey"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="expenses_user_id_fkey"),
        sa.ForeignKeyConstraint(
            ["property_id"], ["properties.id"], name="expenses_property_id_fkey"
        ),
    )

    # ── notifications (estado divergente dos modelos — corrigido em 0003) ──
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("link", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="notifications_pkey"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="notifications_user_id_fkey"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("expenses")
    op.drop_table("payments")
    # Quebrar o ciclo antes de dropar
    op.drop_constraint("fk_tenant_contract_id", "tenants", type_="foreignkey")
    op.drop_constraint("fk_property_tenant_id", "properties", type_="foreignkey")
    op.drop_table("contracts")
    op.drop_table("tenants")
    op.drop_table("properties")
    op.drop_table("users")
