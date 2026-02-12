"""
Supabase Authentication Module

Este módulo gerencia a autenticação usando Supabase Auth.
Substitui o antigo sistema custom de JWT do Auth-API.
"""

from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.core.config import settings
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
    
    Args:
        credentials: Credenciais HTTP Bearer do request
        
    Returns:
        dict: Informações do usuário autenticado
        
    Raises:
        HTTPException: Se o token for inválido ou usuário não encontrado
        
    Exemplo de uso:
        @router.get("/me")
        async def get_me(current_user: dict = Depends(get_current_user)):
            return current_user
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
    Dependency simplificada para obter apenas o ID do usuário
    
    Args:
        current_user: Usuário obtido via get_current_user
        
    Returns:
        str: UUID do usuário
    """
    return current_user["id"]


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency para exigir que o usuário seja admin
    
    Args:
        current_user: Usuário obtido via get_current_user
        
    Returns:
        dict: Informações do usuário admin
        
    Raises:
        HTTPException: Se o usuário não for admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: apenas administradores"
        )
    return current_user


# Funções auxiliares para operações com Supabase Auth

async def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    Busca um usuário pelo ID usando o Supabase
    
    Args:
        user_id: UUID do usuário
        
    Returns:
        dict ou None: Dados do usuário ou None se não encontrado
    """
    try:
        client = get_supabase_client()
        response = client.auth.admin.get_user_by_id(user_id)
        return response.user if response else None
    except Exception as e:
        logger.error(f"Erro ao buscar usuário {user_id}: {str(e)}")
        return None


async def create_user(email: str, password: str, **kwargs) -> dict:
    """
    Cria um novo usuário no Supabase Auth
    
    Args:
        email: Email do usuário
        password: Senha do usuário
        **kwargs: Metadados adicionais (nome, etc)
        
    Returns:
        dict: Dados do usuário criado
        
    Raises:
        HTTPException: Se houver erro na criação
    """
    try:
        client = get_supabase_client()
        response = client.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,  # Auto-confirma email
            "user_metadata": kwargs
        })
        return response.user
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao criar usuário: {str(e)}"
        )


async def update_user_metadata(user_id: str, metadata: dict) -> dict:
    """
    Atualiza metadados de um usuário
    
    Args:
        user_id: UUID do usuário
        metadata: Dicionário com metadados a atualizar
        
    Returns:
        dict: Dados do usuário atualizado
    """
    try:
        client = get_supabase_client()
        response = client.auth.admin.update_user_by_id(
            user_id,
            {"user_metadata": metadata}
        )
        return response.user
    except Exception as e:
        logger.error(f"Erro ao atualizar usuário {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao atualizar usuário: {str(e)}"
        )


async def delete_user(user_id: str) -> bool:
    """
    Deleta um usuário do Supabase Auth
    
    Args:
        user_id: UUID do usuário
        
    Returns:
        bool: True se deletado com sucesso
    """
    try:
        client = get_supabase_client()
        client.auth.admin.delete_user(user_id)
        return True
    except Exception as e:
        logger.error(f"Erro ao deletar usuário {user_id}: {str(e)}")
        return False
