-- ============================================================
-- Políticas de RLS do Supabase Storage — Imobly
-- ============================================================
--
-- COMO APLICAR: cole no SQL Editor do projeto no dashboard do Supabase, ou
-- rode com o DATABASE_URL do projeto. É idempotente: pode reexecutar.
--
-- POR QUE ESTE ARQUIVO EXISTE: as policies vivem no schema `storage`, que
-- pertence ao Supabase e não ao Alembic da aplicação — por isso não são uma
-- migração. Ficam aqui para poder recriá-las num projeto novo. Foi
-- exatamente o que faltou ao migrar para o projeto `imobly-pandafy`: os
-- buckets vieram, as policies não, e `storage.objects` ficou com RLS ativo e
-- zero policies. Resultado: todo upload era negado.
--
-- CONVENÇÃO DO CAMINHO: {auth.uid()}/{categoria}/{entityId}/{arquivo}
-- (ver frontend/lib/services/storage.ts → buildPath). A primeira pasta é o
-- UID do Supabase Auth, e é o que isola um usuário do outro. O frontend
-- obtém esse UID pelo campo `supabase_uid` de /api/v1/auth/me — não use o
-- `id` da resposta, que é o da tabela local e faz o upload ser negado.

-- ── Leitura pelo dono, nos três buckets ──────────────────────
--
-- property-images é bucket público: o download por URL pública não passa por
-- RLS, então é tentador deixá-lo fora daqui. Não deixe. O cliente envia com
-- `upsert: true` e o serviço de Storage faz um SELECT no objeto antes de
-- inserir, para saber se já existe; sem SELECT permitido o upsert falha, e o
-- erro que chega é "new row violates row-level security policy" — que aponta
-- para o INSERT e esconde a causa real. Incluí-lo não expõe nada novo: o
-- conteúdo do bucket já é público por definição.
drop policy if exists "imobly_dono_le_documentos" on storage.objects;
create policy "imobly_dono_le_documentos"
  on storage.objects for select to authenticated
  using (
    bucket_id in ('property-images', 'tenant-documents', 'expense-documents')
    and (storage.foldername(name))[1] = auth.uid()::text
  );

-- ── Envio: só na própria pasta ───────────────────────────────
drop policy if exists "imobly_dono_envia" on storage.objects;
create policy "imobly_dono_envia"
  on storage.objects for insert to authenticated
  with check (
    bucket_id in ('property-images', 'tenant-documents', 'expense-documents')
    and (storage.foldername(name))[1] = auth.uid()::text
  );

-- ── Sobrescrita (o upload usa upsert: true) ──────────────────
drop policy if exists "imobly_dono_atualiza" on storage.objects;
create policy "imobly_dono_atualiza"
  on storage.objects for update to authenticated
  using (
    bucket_id in ('property-images', 'tenant-documents', 'expense-documents')
    and (storage.foldername(name))[1] = auth.uid()::text
  )
  with check (
    bucket_id in ('property-images', 'tenant-documents', 'expense-documents')
    and (storage.foldername(name))[1] = auth.uid()::text
  );

-- ── Exclusão ─────────────────────────────────────────────────
drop policy if exists "imobly_dono_exclui" on storage.objects;
create policy "imobly_dono_exclui"
  on storage.objects for delete to authenticated
  using (
    bucket_id in ('property-images', 'tenant-documents', 'expense-documents')
    and (storage.foldername(name))[1] = auth.uid()::text
  );

-- ── Conferência ──────────────────────────────────────────────
-- Deve listar quatro linhas (SELECT, INSERT, UPDATE, DELETE):
--   select policyname, cmd from pg_policies
--    where schemaname = 'storage' and tablename = 'objects';
