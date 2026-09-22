"""separa cobrança de recebimento (charges + payment_entries)

`payments` tratava um pagamento como um EVENTO único, e por isso não conseguia
representar o caso mais comum da inadimplência: o inquilino que deve 1.000 e
paga 600. Não havia onde guardar o saldo de 400 — `calculo.py` até o calculava,
e o registro o descartava.

Pior, `payments.total_amount` tinha dois significados no mesmo sistema: em
`/register` era o valor PAGO; no painel de inadimplência era lido como o valor
A RECEBER. Quem pagasse 600 de 1.000 aparecia devendo 600.

Agora:

  charges          uma cobrança por (contrato, competência)
  payment_entries  N recebimentos por cobrança

O saldo não é coluna: é `total_devido(data) - soma(recebimentos)`, porque multa
e juros de dívida em aberto crescem todo dia.

MIGRAÇÃO DOS DADOS
Cada pagamento vira uma cobrança da sua competência (mês do vencimento).
Quando há mais de um pagamento para o mesmo contrato no mesmo mês — que era a
única forma de representar pagamento parcelado no modelo antigo — o primeiro
vira a cobrança e os demais viram recebimentos dela, que é o que sempre
significaram.

O valor recebido é reconstruído assim:
  status 'pago'    → amount + fine_amount + interest_amount (o total cobrado)
  status 'parcial' → total_amount (onde `/register` gravava o valor pago)
  demais           → nenhum recebimento

A tabela `payments` NÃO é removida aqui. A aplicação não escreve mais nela, mas
ela continua no banco como rede de segurança da migração; a remoção fica para
uma revisão posterior, depois que os dados convertidos estiverem conferidos em
produção.

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Reconstrução do valor recebido a partir da linha antiga de `payments`.
_VALOR_RECEBIDO = """
    CASE
        WHEN p.status = 'pago'
            THEN COALESCE(p.amount, 0) + COALESCE(p.fine_amount, 0) + COALESCE(p.interest_amount, 0)
        ELSE COALESCE(p.total_amount, 0)
    END
"""


def upgrade() -> None:
    op.create_table(
        "charges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("contract_id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("competencia", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("rent_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("charges_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("discount_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("fine_rate", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("interest_rate", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="aberta"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("canceled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["contract_id"], ["contracts.id"], name="fk_charge_contract_id", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["property_id"], ["properties.id"], name="fk_charge_property_id", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_charge_tenant_id"),
        # Idempotência da geração mensal garantida no BANCO, não só no código:
        # o job automático e o botão manual podem rodar concorrentes.
        sa.UniqueConstraint("contract_id", "competencia", name="ux_charges_contrato_competencia"),
        sa.CheckConstraint(
            "status IN ('aberta','parcial','vencida','quitada','cancelada')",
            name="ck_charges_status",
        ),
    )
    op.create_index("ix_charges_user_id", "charges", ["user_id"])
    op.create_index("ix_charges_contract_id", "charges", ["contract_id"])
    op.create_index("ix_charges_property_id", "charges", ["property_id"])
    op.create_index("ix_charges_tenant_id", "charges", ["tenant_id"])
    op.create_index("ix_charges_competencia", "charges", ["competencia"])
    op.create_index("ix_charges_due_date", "charges", ["due_date"])
    op.create_index("ix_charges_status", "charges", ["status"])
    # Índice composto do caminho quente: "cobranças em aberto do usuário, por
    # vencimento" é a consulta do painel, do aging e do job diário.
    op.create_index("ix_charges_user_status_due", "charges", ["user_id", "status", "due_date"])
    op.create_index("ix_charges_user_tenant", "charges", ["user_id", "tenant_id"])

    op.create_table(
        "payment_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("charge_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("method", sa.String(20), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["charge_id"], ["charges.id"], name="fk_entry_charge_id", ondelete="CASCADE"
        ),
        # Recebimento de valor zero ou negativo não é recebimento. Estorno se
        # faz excluindo a linha, não lançando valor negativo — senão o extrato
        # do inquilino deixa de bater com o que ele efetivamente pagou.
        sa.CheckConstraint("amount > 0", name="ck_payment_entries_amount_positivo"),
    )
    op.create_index("ix_payment_entries_user_id", "payment_entries", ["user_id"])
    op.create_index("ix_payment_entries_charge_id", "payment_entries", ["charge_id"])
    op.create_index("ix_payment_entries_date", "payment_entries", ["date"])
    op.create_index("ix_payment_entries_charge_date", "payment_entries", ["charge_id", "date"])

    # ── Backfill: payments → charges ──
    # DISTINCT ON garante uma cobrança por (contrato, competência); os demais
    # pagamentos do mesmo mês viram recebimentos no passo seguinte.
    op.execute(
        """
        INSERT INTO charges (
            user_id, contract_id, property_id, tenant_id, competencia, due_date,
            rent_amount, charges_amount, discount_amount, fine_rate, interest_rate,
            status, description, created_at, updated_at
        )
        SELECT DISTINCT ON (p.contract_id, date_trunc('month', p.due_date)::date)
            p.user_id,
            p.contract_id,
            p.property_id,
            p.tenant_id,
            date_trunc('month', p.due_date)::date,
            p.due_date,
            COALESCE(p.amount, 0),
            0,
            0,
            COALESCE(c.fine_rate, 0),
            COALESCE(c.interest_rate, 0),
            'aberta',
            'Migrado de payments #' || p.id,
            COALESCE(p.created_at, now()),
            COALESCE(p.updated_at, now())
        FROM payments p
        JOIN contracts c ON c.id = p.contract_id
        ORDER BY p.contract_id, date_trunc('month', p.due_date)::date, p.due_date, p.id
        """
    )

    # ── Backfill: payments → payment_entries ──
    op.execute(
        f"""
        INSERT INTO payment_entries (user_id, charge_id, date, amount, method, description, created_at)
        SELECT
            p.user_id,
            ch.id,
            p.payment_date,
            {_VALOR_RECEBIDO},
            p.payment_method,
            'Migrado de payments #' || p.id,
            COALESCE(p.created_at, now())
        FROM payments p
        JOIN charges ch
          ON ch.contract_id = p.contract_id
         AND ch.competencia = date_trunc('month', p.due_date)::date
        WHERE p.payment_date IS NOT NULL
          AND p.status IN ('pago', 'parcial')
          AND {_VALOR_RECEBIDO} > 0
        """
    )

    # ── Status inicial ──
    # Aproximação deliberada: compara o recebido com o valor BASE, sem recompor
    # multa e juros em SQL. Uma cobrança paga com atraso tem os encargos
    # embutidos no valor migrado, então a comparação com a base continua
    # classificando certo. `sincronizar_status_em_lote` refina no primeiro job
    # diário, e a posição exibida é sempre recalculada na leitura.
    op.execute(
        """
        UPDATE charges ch
        SET status = CASE
            WHEN r.total >= ch.rent_amount THEN 'quitada'
            WHEN r.total > 0 THEN 'parcial'
            WHEN ch.due_date < CURRENT_DATE THEN 'vencida'
            ELSE 'aberta'
        END
        FROM (
            SELECT ch2.id, COALESCE(SUM(pe.amount), 0) AS total
            FROM charges ch2
            LEFT JOIN payment_entries pe ON pe.charge_id = ch2.id
            GROUP BY ch2.id
        ) r
        WHERE r.id = ch.id
        """
    )


def downgrade() -> None:
    # `payments` nunca foi tocada, então o rollback é só descartar o novo.
    # Recebimentos lançados DEPOIS da migração não têm equivalente no modelo
    # antigo e se perdem — é o custo de voltar, e por isso a volta só deve
    # acontecer logo após o deploy.
    op.drop_table("payment_entries")
    op.drop_table("charges")
