# ============================================================
# Script Seguro para Rodar Testes - NUNCA USA BANCO DE PRODUÇÃO
# ============================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  RODANDO TESTES COM BANCO ISOLADO" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Configurar TEST_DATABASE_URL para banco de testes
$env:TEST_DATABASE_URL = "postgresql://postgres:admin123@localhost:5434/imovel_gestao_test"

Write-Host "✅ Banco de testes: $env:TEST_DATABASE_URL`n" -ForegroundColor Green

# Verificar se o container de testes está rodando
$testDbRunning = docker ps --filter "name=imovel_postgres_test" --filter "status=running" -q

if (-not $testDbRunning) {
    Write-Host "⚠️  Container de banco de testes não está rodando!" -ForegroundColor Yellow
    Write-Host "   Iniciando postgres-test...`n" -ForegroundColor Yellow
    
    docker compose up -d postgres-test
    Start-Sleep -Seconds 3
    
    Write-Host "✅ Banco de testes iniciado!`n" -ForegroundColor Green
}

# Rodar testes no container backend
Write-Host "🧪 Executando testes...`n" -ForegroundColor Blue

docker compose exec backend sh -c "TEST_DATABASE_URL=postgresql://postgres:admin123@postgres-test:5432/imovel_gestao_test pytest tests/integration/ -v --tb=short"

$exitCode = $LASTEXITCODE

Write-Host "`n========================================" -ForegroundColor Cyan
if ($exitCode -eq 0) {
    Write-Host "  ✅ TESTES PASSARAM!" -ForegroundColor Green
} else {
    Write-Host "  ❌ TESTES FALHARAM!" -ForegroundColor Red
}
Write-Host "========================================`n" -ForegroundColor Cyan

exit $exitCode
