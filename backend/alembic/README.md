# Migrations (Alembic)

O schema do banco é gerenciado **exclusivamente** aqui. `Base.metadata.create_all()`
foi removido do startup da aplicação (`src/main.py`) e de `src/database.py`: criar
tabelas a partir dos modelos em runtime escondia a divergência entre o ORM e o
banco real — foi a causa-raiz de quatro defeitos de severidade alta na auditoria
(notifications inoperante, unicidade multi-tenant errada, `ON DELETE` fantasma e
timestamps nullable).

## Conexão

Aponte `ALEMBIC_DATABASE_URL` para a conexão **direta** do Postgres (porta 5432).
O pooler do Supabase (porta 6543, *transaction pooling*) não sustenta DDL longo,
advisory locks nem `CREATE INDEX CONCURRENTLY`.

```bash
export ALEMBIC_DATABASE_URL="postgresql://postgres:SENHA@db.<projeto>.supabase.co:5432/postgres"
```

Sem essa variável, o `env.py` cai para `settings.DATABASE_URL`.

## Adoção em um banco que JÁ EXISTE (produção / homologação)

A revisão `0001` é um retrato fiel do schema atual, **com os defeitos**. Ela existe
para ser um ponto comum entre o banco existente e um banco criado do zero — por
isso é marcada, não executada:

```bash
make stamp-baseline     # alembic stamp 0001 — nenhum DDL é executado
make migrate-sql        # revise o SQL das correções pendentes
make migrate            # aplica 0002 em diante
```

> Faça backup antes do `make migrate`. As revisões a partir da 0002 corrigem
> constraints e tipos, e algumas reescrevem dados.

### O que cada revisão faz

| Rev | Efeito | Observação |
|-----|--------|------------|
| 0001 | Baseline — retrato do schema atual, com defeitos | Só `stamp`, nunca executar em banco existente |
| 0002 | `users.supabase_uid` como identidade imutável | Backfill a partir de `hashed_password` |
| 0003 | Corrige `notifications` (`is_read`→`read_status`, colunas ausentes) | Módulo respondia 500 em todos os endpoints |
| 0004 | Unicidade de inquilino por locador, não global | **Aborta se houver duplicatas** dentro do mesmo `user_id` |
| 0005 | `created_at`/`updated_at` NOT NULL com DEFAULT | Preenche nulos existentes |
| 0006 | Políticas `ON DELETE` reais nas FKs | CASCADE / RESTRICT / SET NULL conforme o domínio |
| 0007 | Remove `contracts.titulo` e `titulozin` | **Aborta se estiverem preenchidas** |
| 0008 | Colunas obrigatórias no schema viram NOT NULL no banco | Avisa se `contracts.rent` tiver nulos |

Duas revisões abortam de propósito em vez de "dar um jeito": 0004 (duplicatas
de inquilino) e 0007 (colunas supostamente mortas com dados). Se isso ocorrer,
o dado precisa de decisão humana — resolva e rode de novo.

> **Importante:** o código a partir da Fase 2 depende dessas revisões. Rodar a
> aplicação nova contra um banco ainda na 0001 mantém as notificações
> quebradas, porque as colunas que o repositório consulta só passam a existir
> na 0003.

## Banco novo (dev, CI, teste)

```bash
make migrate            # alembic upgrade head — cria tudo já corrigido
```

A suíte de testes (`tests/conftest.py`) roda `upgrade head` / `downgrade base`
a cada sessão, então uma migration quebrada reprova o build.

## Criar uma migration

```bash
make migration m="adiciona coluna x em contracts"
```

O autogenerate compara `Base.metadata` com o banco. **Sempre revise o arquivo
gerado** — ele não detecta renomeações (vê `DROP` + `ADD`, o que destrói dados),
mudanças de `CHECK`, nem alterações que exijam backfill.

Módulo novo? Importe o modelo em `alembic/env.py`. Sem isso, o autogenerate
propõe dropar as tabelas dele.

## Deploy

`render.yaml` define `preDeployCommand: alembic upgrade head` — as migrations
rodam antes do novo release receber tráfego, e o deploy aborta se falharem.
