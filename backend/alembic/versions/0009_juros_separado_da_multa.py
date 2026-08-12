"""separa juros de multa em payments

`payments.fine_amount` guardava multa + juros somados, então a composição da
cobrança era impossível de reconstruir: não dava para responder "quanto desse
acréscimo foi multa fixa e quanto foi juros pelo tempo de atraso?" — pergunta
corriqueira em contestação de cobrança.

A coluna nova começa zerada. Os registros históricos mantêm o valor agregado
em `fine_amount`; não há como separá-los retroativamente sem recalcular a
partir do contrato e da data de pagamento, o que produziria números que não
foram os efetivamente cobrados. Registro novo já grava separado.

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "payments",
        sa.Column(
            "interest_amount",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("payments", "interest_amount")
