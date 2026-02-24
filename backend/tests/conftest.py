"""
Configuração de testes para a nova arquitetura
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.database import Base, get_db
from src.main import app

# URL do banco de testes
SQLALCHEMY_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql://postgres:admin123@postgres:5432/imovel_gestao_test"
)

# Criar engine para testes
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """Engine de banco para toda a sessão de teste"""
    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    yield engine
    # Limpar após testes
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """Sessão de banco para cada teste"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Cliente de teste FastAPI"""
    
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Headers de autenticação para testes"""
    # Mock token - em testes reais, usar token válido do Supabase
    return {"Authorization": "Bearer test_token"}