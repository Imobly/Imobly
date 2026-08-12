"""alinhar as políticas ON DELETE das FKs ao que os modelos declaram

Os modelos declaram `ondelete="CASCADE"` / `"SET NULL"`, mas no banco todas as
FKs eram NO ACTION (o padrão). O desenvolvedor lê o modelo, acredita no
CASCADE, e o comportamento em produção é o oposto: `DELETE /tenants/{id}` de um
inquilino com contrato devolvia 500 (IntegrityError) em vez de erro tratado.

Políticas aplicadas — escolhidas pelo significado no domínio, não por
conveniência:

  CASCADE (o registro não existe sem o pai)
    contracts.property_id → properties      apagar o imóvel apaga seus contratos
    payments.property_id  → properties
    expenses.property_id  → properties
    payments.contract_id  → contracts       pagamento pertence ao contrato

  RESTRICT (apagar o pai é erro de operação, não uma limpeza silenciosa)
    contracts.tenant_id   → tenants         histórico locatício não some sozinho
    payments.tenant_id    → tenants
    *.user_id             → users           apagar conta exige processo próprio

  SET NULL (o vínculo é opcional)
    properties.tenant_id  → tenants         imóvel sobrevive sem inquilino
    tenants.contract_id   → contracts       inquilino sobrevive sem contrato

  notifications.user_id → users: CASCADE (o modelo já declarava; notificação
    é dado derivado e não deve sobreviver ao dono).

RESTRICT em vez de NO ACTION porque RESTRICT é checado imediatamente, dando um
erro mais previsível — a camada de aplicação traduz para 409.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-12

"""

from typing import Sequence, Union

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (constraint, tabela, coluna, tabela_ref, ondelete_novo, ondelete_antigo)
_FKS = [
    ("fk_contract_property_id", "contracts", "property_id", "properties", "CASCADE", None),
    ("fk_contract_tenant_id", "contracts", "tenant_id", "tenants", "RESTRICT", None),
    ("contracts_user_id_fkey", "contracts", "user_id", "users", "RESTRICT", None),
    ("payments_property_id_fkey", "payments", "property_id", "properties", "CASCADE", None),
    ("payments_contract_id_fkey", "payments", "contract_id", "contracts", "CASCADE", None),
    ("payments_tenant_id_fkey", "payments", "tenant_id", "tenants", "RESTRICT", None),
    ("payments_user_id_fkey", "payments", "user_id", "users", "RESTRICT", None),
    ("expenses_property_id_fkey", "expenses", "property_id", "properties", "CASCADE", None),
    ("expenses_user_id_fkey", "expenses", "user_id", "users", "RESTRICT", None),
    ("properties_user_id_fkey", "properties", "user_id", "users", "RESTRICT", None),
    ("fk_property_tenant_id", "properties", "tenant_id", "tenants", "SET NULL", None),
    ("tenants_user_id_fkey", "tenants", "user_id", "users", "RESTRICT", None),
    ("fk_tenant_contract_id", "tenants", "contract_id", "contracts", "SET NULL", None),
    ("notifications_user_id_fkey", "notifications", "user_id", "users", "CASCADE", None),
]


def _recriar(constraint, tabela, coluna, tabela_ref, ondelete):
    op.drop_constraint(constraint, tabela, type_="foreignkey")
    op.create_foreign_key(
        constraint,
        tabela,
        tabela_ref,
        [coluna],
        ["id"],
        ondelete=ondelete,
    )


def upgrade() -> None:
    for constraint, tabela, coluna, tabela_ref, novo, _antigo in _FKS:
        _recriar(constraint, tabela, coluna, tabela_ref, novo)


def downgrade() -> None:
    for constraint, tabela, coluna, tabela_ref, _novo, antigo in _FKS:
        _recriar(constraint, tabela, coluna, tabela_ref, antigo)
