-- ============================================================
-- Migration: Índice ÚNICO em users(email)
-- ------------------------------------------------------------
-- O modelo SQLAlchemy (auth/models.py) declara email como unique=True,
-- mas o schema real (DDL.sql) foi criado sem esse índice. Toda requisição
-- autenticada resolve o usuário por email (get_current_user_local_id),
-- então a ausência do índice gera full scans desnecessários.
--
-- Cria o índice único de forma idempotente. Caso existam emails duplicados,
-- a criação falhará — resolva os duplicados antes de aplicar.
-- ============================================================

BEGIN;

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email_unique
    ON public.users (email);

COMMIT;
