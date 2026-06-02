-- ============================================================
-- Migration: Atualizar status de contratos, pagamentos e
-- adicionar coluna due_day em contratos
-- ============================================================

BEGIN;

-- 1. Atualizar status dos contratos (inglês → português)
UPDATE contracts SET status = 'ativo'    WHERE status = 'active';
UPDATE contracts SET status = 'expirado' WHERE status = 'expired';
UPDATE contracts SET status = 'inativo'  WHERE status = 'terminated';

-- 2. Remover coluna status dos inquilinos (agora derivado do contrato)
ALTER TABLE tenants DROP COLUMN IF EXISTS status;

-- 3. Atualizar status dos pagamentos (inglês → português)
UPDATE payments SET status = 'pago'      WHERE status = 'paid';
UPDATE payments SET status = 'pendente'  WHERE status = 'pending';
UPDATE payments SET status = 'atrasado'  WHERE status = 'overdue';
UPDATE payments SET status = 'parcial'   WHERE status = 'partial';

-- 4. Adicionar coluna due_day na tabela contracts
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS due_day INTEGER;

COMMIT;
