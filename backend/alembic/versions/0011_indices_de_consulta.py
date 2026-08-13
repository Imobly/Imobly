"""índices de suporte às consultas reais da aplicação

Os modelos declaravam `index=True` em várias colunas, mas o banco real não
tinha nenhum índice além das chaves primárias e de um em notifications: os
`index=True` nunca viraram DDL porque o schema foi criado fora do ORM.

Resultado: toda agregação do dashboard fazia sequential scan da tabela
inteira. Com poucos milhares de linhas passa despercebido; com centenas de
milhares, o endpoint mais acessado do sistema degrada de milissegundos para
segundos e satura o pool de conexões.

Os índices seguem as consultas que existem de fato — todas começam por
`user_id`, porque todo acesso é filtrado pelo dono:

  properties: status (dashboard), tenant_id (vínculo)
  payments:   status, due_date, payment_date (receita do mês), tenant_id
  contracts:  status+end_date (alertas de vencimento), property_id, tenant_id
  expenses:   date (despesa do mês), property_id, status

Dois são PARCIAIS: `ix_payments_pagos_por_data` e `ix_contracts_ativos_fim`
cobrem só as linhas que as consultas usam ('pago' e 'ativo'). Índice parcial
ocupa menos espaço e é mais rápido de manter na escrita.

`CREATE INDEX` normal, não `CONCURRENTLY`: o Alembic roda cada revisão dentro
de uma transação, e CONCURRENTLY não pode. Em produção com tabela grande e
tráfego, prefira aplicar estes CONCURRENTLY manualmente e depois `alembic
stamp 0011` — as tabelas aqui são pequenas o bastante para o lock ser
irrelevante.

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (nome, tabela, colunas, condição parcial)
_INDICES = [
    ("ix_properties_user_status", "properties", ["user_id", "status"], None),
    ("ix_properties_user_tenant", "properties", ["user_id", "tenant_id"], None),

    ("ix_payments_user_status", "payments", ["user_id", "status"], None),
    ("ix_payments_user_due_date", "payments", ["user_id", "due_date"], None),
    ("ix_payments_user_tenant", "payments", ["user_id", "tenant_id"], None),
    ("ix_payments_user_property", "payments", ["user_id", "property_id"], None),
    ("ix_payments_user_contract", "payments", ["user_id", "contract_id"], None),
    # Receita do mês filtra status='pago' e agrupa por payment_date.
    (
        "ix_payments_pagos_por_data",
        "payments",
        ["user_id", "payment_date"],
        "status = 'pago'",
    ),

    ("ix_contracts_user_status", "contracts", ["user_id", "status"], None),
    ("ix_contracts_user_property", "contracts", ["user_id", "property_id"], None),
    ("ix_contracts_user_tenant", "contracts", ["user_id", "tenant_id"], None),
    # Alertas de vencimento: contratos ativos ordenados por fim de vigência.
    (
        "ix_contracts_ativos_fim",
        "contracts",
        ["user_id", "end_date"],
        "status = 'ativo'",
    ),

    ("ix_expenses_user_date", "expenses", ["user_id", "date"], None),
    ("ix_expenses_user_property", "expenses", ["user_id", "property_id"], None),
    ("ix_expenses_user_status", "expenses", ["user_id", "status"], None),
]


def upgrade() -> None:
    for nome, tabela, colunas, condicao in _INDICES:
        op.create_index(
            nome,
            tabela,
            colunas,
            postgresql_where=sa.text(condicao) if condicao else None,
        )


def downgrade() -> None:
    for nome, tabela, _colunas, _condicao in reversed(_INDICES):
        op.drop_index(nome, table_name=tabela)
