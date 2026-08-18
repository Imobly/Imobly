"""
Configuração do banco de dados SQLAlchemy
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from src.config import settings

# Base class para todos os modelos SQLAlchemy
Base = declarative_base()

# NullPool deixou de ser o padrão. O raciocínio anterior ("o PgBouncer já faz
# pool, então não segure conexões") confunde duas camadas: o PgBouncer
# multiplexa as conexões *dele* com o Postgres, mas a conexão
# aplicação→PgBouncer continua sendo TCP + TLS + handshake de autenticação a
# cada request. Contra o pooler do Supabase em outra região isso é caro —
# medido daqui: ~210-280ms só no handshake TCP, antes de TLS e auth.
#
# Manter um QueuePool contra o PgBouncer em modo *transaction* é seguro desde
# que não se dependa de estado de sessão (SET, temp tables) nem de prepared
# statements do lado do servidor — o SQLAlchemy com psycopg2 não usa nenhum
# dos dois por padrão, e este projeto não usa.
#
# `DB_USE_NULLPOOL=true` continua disponível para ambientes serverless, onde
# o processo morre entre requisições e um pool nunca é reaproveitado.
use_nullpool = os.getenv("DB_USE_NULLPOOL", "false").lower() == "true"

# `pool_pre_ping` gasta um round-trip (SELECT 1) a cada checkout — ~200ms com
# o banco em us-west-2. Preferimos reciclar as conexões preventivamente, com
# um `pool_recycle` bem abaixo do idle timeout do pooler, a pagar esse ping em
# toda requisição. Quem estiver num ambiente instável pode religar via env.
usar_pre_ping = os.getenv("DB_POOL_PRE_PING", "false").lower() == "true"

if use_nullpool:
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
        echo=settings.DEBUG,
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        # Reciclagem curta: precisa ser MENOR que o idle timeout do PgBouncer,
        # senão o pool devolve uma conexão que o servidor já fechou.
        pool_recycle=min(settings.DB_POOL_RECYCLE, 240),
        pool_pre_ping=usar_pre_ping,
        echo=settings.DEBUG,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency para obter sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# NOTA: não existe mais `create_tables()`. O schema é gerenciado exclusivamente
# pelo Alembic (`make migrate` / `alembic upgrade head`). Criar tabelas a partir
# dos modelos em runtime escondia divergências entre o ORM e o banco real.
