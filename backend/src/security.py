"""
Módulo de segurança e autenticação

Lógica de JWT, hash de senha e autenticação via Supabase
"""

import threading
from typing import Optional

from cachetools import TTLCache
from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from supabase import create_client, Client

from src.config import settings
from src.database import get_db
from src.core.supabase_storage_service import SupabaseStorageService
import jwt
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer security scheme
security = HTTPBearer()

# Cliente Supabase
supabase: Optional[Client] = None


def get_supabase_client() -> Client:
    """Retorna o cliente Supabase"""
    global supabase
    if supabase is None:
        supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
    return supabase


def get_storage_service(supabase: Client = Depends(get_supabase_client)) -> SupabaseStorageService:
    """Retorna o serviço de storage do Supabase"""
    return SupabaseStorageService(supabase)


async def verify_jwt_token(token: str) -> dict:
    """
    Verifica e decodifica o JWT token do Supabase
    
    Args:
        token: JWT token do Supabase
        
    Returns:
        dict: Payload do token decodificado
        
    Raises:
        HTTPException: Se o token for inválido
    """
    try:
        # Supabase usa HS256 com JWT_SECRET (não RS256/JWKS)
        # O segredo JWT é derivado do SUPABASE_JWT_SECRET
        # Decodifica e valida o token
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_exp": True}
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    except Exception as e:
        logger.error(f"Erro ao verificar token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erro ao verificar token"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency para obter o usuário atual autenticado
    """
    token = credentials.credentials
    
    # Verifica o JWT
    payload = await verify_jwt_token(token)
    
    # Extrai informações do usuário
    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role", "authenticated")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não identificado no token"
        )
    
    return {
        "id": user_id,
        "email": email,
        "role": role,
        "payload": payload
    }


async def get_current_user_id(
    current_user: dict = Depends(get_current_user)
) -> str:
    """
    Dependency simplificada para obter apenas o ID do usuário (UUID do Supabase)
    """
    return current_user["id"]


# Cache em processo do mapeamento UUID do Supabase -> id local. Evita repetir o
# SELECT FROM users em cada request — relevante quando o frontend dispara
# várias chamadas em paralelo (ex.: dashboard).
#
# Era um `dict` sem limite e sem expiração: crescia indefinidamente enquanto o
# processo vivesse (um item por usuário que já acessou) e nunca refletia
# mudanças feitas no banco — desativar uma conta não tinha efeito até reiniciar.
#
# TTL curto porque a resolução é barata: o ganho é absorver a rajada de
# requisições paralelas de um mesmo carregamento de tela, não guardar estado
# por horas. `maxsize` transforma o vazamento num teto previsível.
_local_id_cache: TTLCache = TTLCache(maxsize=10_000, ttl=300)

# O cache é lido e escrito por várias threads (FastAPI roda dependências
# síncronas em threadpool); `TTLCache` não é thread-safe por si só.
_cache_lock = threading.Lock()


def invalidar_cache_de_identidade(supabase_uid: str | None = None) -> None:
    """
    Remove uma entrada (ou todas) do cache de identidade.

    Necessário quando o vínculo usuário↔registro local muda — hoje, ao
    reivindicar o `supabase_uid` de uma linha legada.
    """
    with _cache_lock:
        if supabase_uid is None:
            _local_id_cache.clear()
        else:
            _local_id_cache.pop(supabase_uid, None)


def _resolver_usuario_local(db: Session, supabase_uid: str, email: str):
    """
    Resolve (ou cria) o registro local correspondente à identidade do Supabase.

    Três caminhos, nesta ordem:
      1. Pela chave imutável `supabase_uid` — o caso normal.
      2. Linha legada, anterior à coluna: localiza por e-mail UMA vez e
         reivindica o uid, migrando a identidade.
      3. Primeiro acesso: cria o registro.

    Extraído de `get_current_user_local_id` para manter aquela dependency
    legível — a lógica de resolução tem ramificações demais para conviver com
    o cache e as checagens de acesso no mesmo corpo.
    """
    from src.auth.models import User

    user = db.query(User).filter(User.supabase_uid == supabase_uid).first()
    if user is not None:
        return user

    legacy = db.query(User).filter(User.email == email).first()
    if legacy is not None:
        if legacy.supabase_uid and legacy.supabase_uid != supabase_uid:
            # O e-mail pertence a outra identidade do Supabase. Nunca sequestre
            # a linha — falhe alto para investigação.
            logger.error(
                "Conflito de identidade: e-mail %s pertence ao uid %s, token traz %s",
                email, legacy.supabase_uid, supabase_uid,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflito de identidade da conta. Contate o suporte.",
            )
        legacy.supabase_uid = supabase_uid
        db.commit()
        db.refresh(legacy)
        # O vínculo mudou: descarta qualquer resolução anterior.
        invalidar_cache_de_identidade(supabase_uid)
        logger.info("Identidade migrada para supabase_uid: %s (id=%s)", email, legacy.id)
        return legacy

    username = email.split("@")[0]
    user = User(
        supabase_uid=supabase_uid,
        email=email,
        username=username,
        full_name=username,
        hashed_password=supabase_uid,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        # Requisições concorrentes do mesmo usuário novo (o dashboard dispara
        # várias em paralelo): a outra venceu a corrida — releia a linha dela.
        db.rollback()
        user = db.query(User).filter(User.supabase_uid == supabase_uid).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Não foi possível provisionar o usuário",
            )
        return user

    logger.info("Usuário local criado automaticamente: %s (id=%s)", email, user.id)
    return user


async def get_current_user_local_id(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> int:
    """
    Dependency para obter o ID integer do usuário na tabela local.
    O resultado é cacheado em request.state (por requisição) e em um cache
    de processo por UUID do Supabase (entre requisições).
    """
    # Retorna do cache se já resolvido nesta requisição
    if hasattr(request.state, "user_local_id"):
        return request.state.user_local_id

    supabase_uid = current_user["id"]

    # Cache entre requisições (UUID -> id local), com TTL curto
    with _cache_lock:
        cached = _local_id_cache.get(supabase_uid)
    if cached is not None:
        request.state.user_local_id = cached
        return cached

    email = current_user.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email não encontrado no token"
        )

    user = _resolver_usuario_local(db, supabase_uid, email)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada",
        )

    # Armazena no cache de processo e no estado da requisição para reutilização
    with _cache_lock:
        _local_id_cache[supabase_uid] = user.id
    request.state.user_local_id = user.id
    return user.id


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency para exigir que o usuário seja admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: permissões de admin necessárias"
        )
    return current_user
