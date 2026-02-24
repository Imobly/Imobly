"""
Módulo de segurança e autenticação

Lógica de JWT, hash de senha e autenticação via Supabase
"""

from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
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


async def get_current_user_local_id(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> int:
    """
    Dependency para obter o ID integer do usuário na tabela local
    """
    from src.auth.models import User
    
    email = current_user.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email não encontrado no token"
        )
    
    # Busca usuário na tabela local
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Se não existe, cria com as informações disponíveis
        supabase_id = current_user["id"]
        username = email.split("@")[0]
        
        user = User(
            email=email,
            username=username,
            full_name=username,
            hashed_password=supabase_id,
            is_active=True,
            is_superuser=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Usuário local criado automaticamente: {email} (id={user.id})")
    
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