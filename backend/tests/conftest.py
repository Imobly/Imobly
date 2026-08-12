"""
Configuração de testes para a nova arquitetura
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.database import get_db
from src.main import app

# URL do banco de testes
SQLALCHEMY_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:admin123@postgres:5432/imovel_gestao_test"
)

# Criar engine para testes
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

BACKEND_ROOT = Path(__file__).parent.parent


def _alembic_config() -> Config:
    """Config do Alembic apontada para o banco de testes."""
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    # env.py lê ALEMBIC_DATABASE_URL com prioridade
    os.environ["ALEMBIC_DATABASE_URL"] = SQLALCHEMY_DATABASE_URL
    return cfg


@pytest.fixture(scope="session")
def db_engine():
    """
    Engine de banco para toda a sessão de teste.

    O schema é construído pelas MIGRATIONS, não por `metadata.create_all`.
    Assim a suíte falha se uma migration quebrar — que era exatamente a classe
    de defeito invisível antes do Alembic.
    """
    cfg = _alembic_config()
    command.upgrade(cfg, "head")
    yield engine
    command.downgrade(cfg, "base")


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


# ---------------------------------------------------------------------------
# Fixtures de multi-tenant — autenticação REAL (dependency override)
#
# As fixtures acima produzem requisições não autenticadas: os testes que as
# usam aceitam 401 como sucesso e, por isso, não verificam comportamento algum.
# As fixtures abaixo injetam um usuário concreto, permitindo asserções de
# isolamento entre inquilinos do SaaS.
# ---------------------------------------------------------------------------

@pytest.fixture
def make_user(db_session):
    """Cria um usuário local e devolve o registro."""
    from src.auth.models import User

    created = []

    def _make(email: str, uid: str) -> "User":
        user = User(
            supabase_uid=uid,
            email=email,
            username=email.split("@")[0],
            full_name=email.split("@")[0],
            hashed_password=uid,
            is_active=True,
            is_superuser=False,
        )
        db_session.add(user)
        db_session.flush()
        created.append(user)
        return user

    return _make


@pytest.fixture
def client_as(db_session):
    """
    Devolve um TestClient autenticado como o `user_id` informado.

    Substitui `get_current_user_local_id` diretamente: o objetivo é testar as
    regras de autorização dos endpoints, não a validação de JWT do Supabase.
    """
    from src.security import get_current_user_local_id

    def _client_as(user_id: int) -> TestClient:
        def override_get_db():
            return db_session

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user_local_id] = lambda: user_id
        return TestClient(app)

    yield _client_as
    app.dependency_overrides.clear()