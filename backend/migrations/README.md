# SQL legado — superado pelo Alembic

Os arquivos `.sql` deste diretório são **históricos**. Não os execute.

| Arquivo | Situação |
|---|---|
| `update_status_enum.sql` | Já aplicado; o efeito (coluna `due_day`, status em português, remoção de `tenants.status`) está refletido no baseline `alembic/versions/0001_*.py`. |
| `add_users_email_unique_index.sql` | Substituído pela revisão Alembic que trata a identidade de usuários. |

Novas alterações de schema vão em `backend/alembic/versions/` — veja
[`../alembic/README.md`](../alembic/README.md).
