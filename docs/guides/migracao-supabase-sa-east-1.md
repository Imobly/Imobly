# Migração do Supabase para sa-east-1 (São Paulo)

**Motivo:** o projeto está em `us-west-2` (Oregon). RTT medido daqui: **~200ms por
round-trip**. Em `sa-east-1` isso cai para ~10–20ms — ganho de ordem de magnitude,
maior que qualquer otimização de código.

O Supabase **não permite trocar a região de um projeto existente**. O caminho é
criar um projeto novo em `sa-east-1` e migrar os dados.

---

## Levantamento (feito em 2026-08-18)

| item | valor |
|---|---|
| Tamanho total do banco | 13 MB |
| `auth.users` | 5 (todos com e-mail/senha) |
| `auth.identities` | 5 |
| `public.users` | 6 → **3 com `supabase_uid`**, **3 legadas sem uid** |
| uid órfão (aponta para auth inexistente) | 0 |
| Objetos no Storage | 4 (162 kB) |
| Linhas com URL do Storage embutida | 4 (3 `properties.images` + 1 `tenants.documents`) |
| Postgres do servidor | **17.6** |

O volume é trivial. **O risco não está nos dados — está na identidade e na config.**

---

## Armadilha nº 1 (a mais séria): os UUIDs de `auth.users` PRECISAM ser preservados

`src/security.py` resolve o usuário local por `supabase_uid`. Se não encontra,
tenta por e-mail e então:

```python
if legacy.supabase_uid and legacy.supabase_uid != supabase_uid:
    raise HTTPException(status_code=409, detail="Conflito de identidade da conta...")
```

Se a migração gerar **novos** UUIDs, as 3 linhas de `public.users` já vinculadas
passam a apontar para UUIDs inexistentes. No primeiro login, o código cai no
caminho por e-mail, vê o uid divergente e devolve **409 permanente** — o usuário
fica trancado fora, e só sai disso com intervenção manual no banco.

**Portanto:** a migração de `auth.users` tem que preservar a coluna `id`.
Um `INSERT` com os UUIDs originais resolve; recriar usuários pela UI/API **não**.

## Armadilha nº 2: o ref do projeto está gravado dentro do banco

4 linhas têm URLs do Storage com o ref antigo (`yyeldattafklyutbbnhu`) embutido em
colunas JSON. Após migrar, essas URLs apontam para o projeto velho — que você vai
querer desligar. Precisam ser reescritas (passo 7).

## Armadilha nº 3: `pg_dump` local é incompatível

```
pg_dump: error: aborting because of server version mismatch
pg_dump: detail: server version: 17.6; pg_dump version: 16.14
```

Instale o client 17 antes de qualquer coisa:

```bash
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/pgdg.gpg
sudo apt update && sudo apt install -y postgresql-client-17
pg_dump --version   # deve dizer 17.x
```

## Armadilha nº 4: use a porta de sessão, não a de transação

`pg_dump`/`pg_restore` não funcionam de forma confiável pelo PgBouncer em modo
transaction (porta **6543**). Use a **5432** (session mode) para o dump e o restore.
A aplicação continua na 6543.

---

## Procedimento

> Faça em janela de manutenção. O `SUPABASE_JWT_SECRET` muda com o projeto novo,
> então **todas as sessões ativas caem** e todos precisam logar de novo — isso é
> esperado e inevitável.

### 1. Criar o projeto novo
No dashboard do Supabase: **New project** → região **South America (São Paulo)
`sa-east-1`**. Guarde project ref, senha do banco, `anon key`, `service_role key`
e o `JWT secret`.

### 2. Backup do projeto atual (com o client 17)

```bash
cd backend
export $(grep -E "^DATABASE_URL=" .env | xargs -d '\n')
# troque a porta 6543 -> 5432 (session mode)
export URL_ORIGEM=$(echo "$DATABASE_URL" | sed 's/:6543/:5432/')

mkdir -p ~/migracao-supabase && cd ~/migracao-supabase

# Dados de negócio (schema public)
pg_dump "$URL_ORIGEM" --schema=public --no-owner --no-privileges -Fc -f public.dump

# Identidade — SÓ as tabelas necessárias, preservando os UUIDs
pg_dump "$URL_ORIGEM" --data-only --no-owner \
  -t auth.users -t auth.identities -Fc -f auth.dump
```

Confira que os arquivos não estão vazios antes de seguir.

### 3. Baixar os 4 arquivos do Storage
São 162 kB. Pelo dashboard (Storage → bucket `users` → download) ou via CLI.
Preserve a estrutura de pastas `{user_id}/{categoria}/{arquivo}`.

### 4. Aplicar as migrations no projeto novo

Não restaure o schema do dump — deixe o Alembic construí-lo, que é a fonte de
verdade do projeto:

```bash
cd ~/projects/Imobly-Monorepo/backend
ALEMBIC_DATABASE_URL="<URL_DESTINO_porta_5432>" alembic upgrade head
```

### 5. Restaurar identidade preservando UUIDs

```bash
cd ~/migracao-supabase
pg_restore --data-only --no-owner -d "<URL_DESTINO_porta_5432>" auth.dump
```

Se houver conflito de chave, é porque o projeto novo já criou usuários — apague-os
pelo dashboard antes e repita. **Nunca** deixe o restore gerar ids novos.

### 6. Restaurar os dados de negócio

```bash
pg_restore --data-only --no-owner --disable-triggers \
  -d "<URL_DESTINO_porta_5432>" public.dump
```

### 7. Reescrever as URLs do Storage (as 4 linhas)

Depois de reenviar os arquivos ao bucket do projeto novo:

```sql
-- confira antes:
select id, images from public.properties where images::text like '%REF_ANTIGO%';

update public.properties
   set images = replace(images::text, 'REF_ANTIGO', 'REF_NOVO')::jsonb
 where images::text like '%REF_ANTIGO%';

update public.tenants
   set documents = replace(documents::text, 'REF_ANTIGO', 'REF_NOVO')::jsonb
 where documents::text like '%REF_ANTIGO%';
```

> Ajuste o cast (`::jsonb` / `::json`) ao tipo real da coluna.

### 8. Atualizar a configuração

`backend/.env`:
- `DATABASE_URL` → novo host `aws-0-sa-east-1.pooler.supabase.com:6543`
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`

`frontend/.env`:
- `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`

`backend/render.yaml` — **contém um `DATABASE_URL` de us-west-2 hardcoded**; se
esquecer dele, a produção continua apontando para o projeto antigo.

Criar o bucket `users` no projeto novo, com as mesmas políticas de acesso.

### 9. Verificação

```bash
# RTT — deve cair de ~200ms para ~10-20ms
export $(grep -E "^DATABASE_URL=" backend/.env | xargs -d '\n')
psql "$DATABASE_URL" -c "\timing on" -c "select 1;"
```

Confira as contagens contra a tabela do levantamento (5 auth.users, 6 public.users,
7 tenants, 8 properties, 6 contracts, 4 payments, 3 expenses) e que os 3
`supabase_uid` continuam casando:

```sql
select count(*) from public.users u join auth.users a on a.id = u.supabase_uid;
-- deve retornar 3
```

Com `PERF_PROFILING=true` no backend, compare o `[PERF] total da rota` de um
salvamento antes/depois.

### 10. Só então desligue o projeto antigo
Mantenha-o pausado (não deletado) por alguns dias, até confirmar que nada quebrou.

---

## Depois da migração

Com RTT de ~15ms, revisite `backend/src/database.py`: o `pool_recycle` curto e o
`pool_pre_ping=False` foram escolhas feitas para latência alta. Com o banco perto,
`pool_pre_ping=True` volta a ser barato e mais seguro.
