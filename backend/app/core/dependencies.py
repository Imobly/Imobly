"""
FastAPI dependencies para autenticação com Auth-api externo
"""
from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth_client import get_current_user_id

# Security scheme for JWT Bearer token
security = HTTPBearer()


async def get_current_user_id_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    """
    Extrai user_id do JWT token do Auth-api

    Args:
        credentials: Bearer token credentials

    Returns:
        user_id do usuário autenticado

    Raises:
        HTTPException: 401 se token inválido
    """
    token = credentials.credentials
    return get_current_user_id(token)


async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[int]:
    """
    Extrai user_id do token se presente, retorna None se não autenticado

    Args:
        credentials: Bearer token credentials (opcional)

    Returns:
        user_id ou None
    """
    if credentials is None:
        return None

    from app.core.auth_client import get_user_id_from_token

    return get_user_id_from_token(credentials.credentials)
