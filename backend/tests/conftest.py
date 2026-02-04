"""Pytest configuration and fixtures"""

import os
import sys
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# ============ PROTEÇÃO CONTRA USO DE BANCO DE PRODUÇÃO ============

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
PRODUCTION_DATABASE_URL = os.getenv("DATABASE_URL")

# VALIDAÇÃO 1: TEST_DATABASE_URL deve estar definido
if not TEST_DATABASE_URL:
    print("\n" + "=" * 80)
    print("❌ ERRO: TEST_DATABASE_URL não está definido!")
    print("=" * 80)
    print("\nPara rodar os testes, você DEVE definir uma URL de banco SEPARADA.")
    print("\nExemplos:")
    print("  Windows PowerShell:")
    print(
        '    $env:TEST_DATABASE_URL="postgresql://postgres:admin123@localhost:5432/imovel_gestao_test"'
    )
    print("\n  Linux/Mac:")
    print(
        '    export TEST_DATABASE_URL="postgresql://postgres:admin123@localhost:5432/imovel_gestao_test"'
    )
    print("\n  Docker Compose:")
    print(
        '    docker compose exec backend sh -c "TEST_DATABASE_URL=postgresql://postgres:admin123@postgres:5432/imovel_gestao_test pytest"'
    )
    print("\n" + "=" * 80)
    sys.exit(1)

# VALIDAÇÃO 2: TEST_DATABASE_URL deve ser diferente de DATABASE_URL
if PRODUCTION_DATABASE_URL and TEST_DATABASE_URL == PRODUCTION_DATABASE_URL:
    print("\n" + "=" * 80)
    print("❌ ERRO: TEST_DATABASE_URL é igual a DATABASE_URL (produção)!")
    print("=" * 80)
    print("\nVocê está tentando rodar testes no BANCO DE PRODUÇÃO.")
    print("Isso pode APAGAR TODOS OS SEUS DADOS!")
    print("\nUse um banco diferente para testes.")
    print(f"\n  Produção: {PRODUCTION_DATABASE_URL}")
    print(f"  Testes:   {TEST_DATABASE_URL}")
    print("\n" + "=" * 80)
    sys.exit(1)

# VALIDAÇÃO 3: Se for Postgres, garantir que o nome do banco termina com '_test'
if TEST_DATABASE_URL.startswith("postgresql"):
    if not ("_test" in TEST_DATABASE_URL or ":memory:" in TEST_DATABASE_URL):
        print("\n" + "=" * 80)
        print("⚠️  AVISO: O nome do banco de testes deve conter '_test'")
        print("=" * 80)
        print(f"\n  URL atual: {TEST_DATABASE_URL}")
        print("\n  Recomendado: postgresql://user:pass@host:port/imovel_gestao_test")
        print("\n" + "=" * 80)
        response = input("\nContinuar mesmo assim? (digite 'SIM' para confirmar): ")
        if response != "SIM":
            sys.exit(1)

print(f"\n✅ Testes rodando em: {TEST_DATABASE_URL}\n")

if TEST_DATABASE_URL.startswith("sqlite"):
    # SQLite in-memory (uso local) – atenção: tipos específicos (JSONB) não são suportados
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # Postgres (CI/CD)
    engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test in isolated schema"""
    from sqlalchemy import text

    # Para Postgres, usar schema isolado 'test_schema'
    if TEST_DATABASE_URL.startswith("postgresql"):
        with engine.connect() as conn:
            # Criar schema de teste isolado
            conn.execute(text("DROP SCHEMA IF EXISTS test_schema CASCADE"))
            conn.execute(text("CREATE SCHEMA test_schema"))
            conn.execute(text("SET search_path TO test_schema"))
            conn.commit()

    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    # Para Postgres, configurar o search_path na sessão
    if TEST_DATABASE_URL.startswith("postgresql"):
        db.execute(text("SET search_path TO test_schema"))
        db.commit()

    try:
        yield db
    finally:
        db.close()
        # Cleanup: Drop schema de teste
        with engine.connect() as conn:
            if TEST_DATABASE_URL.startswith("postgresql"):
                # Postgres: drop APENAS o schema de teste
                conn.execute(text("DROP SCHEMA IF EXISTS test_schema CASCADE"))
                conn.commit()
            else:
                # SQLite: regular drop_all
                Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with the test database and mocked auth"""
    from app.core.dependencies import get_current_user_id_from_token

    # Limpar os event handlers do startup para evitar create_tables no banco errado
    app.router.on_startup = []

    # Garantir que o diretório de uploads existe (necessário para StaticFiles)
    from app.core.config import settings

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    def override_get_current_user():
        """Mock user_id for tests - simulates authenticated user"""
        return 1  # Default test user_id

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id_from_token] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_property_data():
    """Sample property data for tests"""
    return {
        "user_id": 1,  # Required for multi-tenancy
        "name": "Test Property",
        "address": "Test Address, 123",
        "neighborhood": "Test Neighborhood",
        "city": "Test City",
        "state": "TS",
        "zip_code": "12345-678",
        "type": "apartment",
        "area": 80.0,
        "bedrooms": 2,
        "bathrooms": 1,
        "parking_spaces": 1,
        "rent": 1500.00,
        "status": "vacant",
        "description": "Test description",
        "is_residential": True,
    }


@pytest.fixture
def sample_tenant_data():
    """Sample tenant data for tests"""
    return {
        "user_id": 1,  # Required for multi-tenancy
        "name": "Test Tenant",
        "email": "test@example.com",
        "phone": "+5511999999999",
        "cpf_cnpj": "12345678901",
        "profession": "Software Engineer",
        "status": "active",
    }


@pytest.fixture
def sample_unit_data():
    """Sample unit data for tests"""
    return {
        "property_id": 1,
        "number": "101",
        "area": 75.5,
        "bedrooms": 2,
        "bathrooms": 1,
        "rent": 1500.00,
        "status": "vacant",
    }


@pytest.fixture
def sample_contract_data():
    """Sample contract data for tests"""
    from datetime import date

    return {
        "user_id": 1,  # Required for multi-tenancy
        "title": "Test Contract",
        "property_id": 1,
        "tenant_id": 1,
        "start_date": date(2025, 1, 1),
        "end_date": date(2026, 1, 1),
        "rent": 1500.00,
        "deposit": 1500.00,
        "interest_rate": 1.0,
        "fine_rate": 2.0,
        "status": "active",
    }


@pytest.fixture
def sample_payment_data():
    """Sample payment data for tests"""
    from datetime import date

    return {
        "user_id": 1,  # Required for multi-tenancy
        "property_id": 1,
        "tenant_id": 1,
        "contract_id": 1,
        "due_date": date(2025, 1, 5),
        "amount": 1500.00,
        "fine_amount": 0.0,
        "total_amount": 1500.00,
        "status": "pending",
    }


@pytest.fixture
def sample_expense_data():
    """Sample expense data for tests"""
    from datetime import date

    return {
        "user_id": 1,  # Required for multi-tenancy
        "property_id": 1,
        "type": "expense",
        "description": "Test Expense",
        "amount": 250.00,
        "category": "maintenance",
        "date": date(2025, 1, 10),
        "status": "pending",
    }


# ============ Authentication Fixtures ============


# NOTE: Auth fixtures removed - authentication managed by separate Auth-api service
# Old fixtures: sample_user_data, sample_user, auth_headers, superuser_data, superuser, superuser_headers
