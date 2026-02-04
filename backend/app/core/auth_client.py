"""
Cliente para validação de JWT tokens do Auth-api
"""
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica e valida um JWT token

    Args:
        token: JWT token para decodificar

    Returns:
        Payload do token ou None se inválido
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return dict(payload) if payload else None
    except JWTError:
        return None


def get_user_id_from_token(token: str) -> Optional[int]:
    """
    Extrai o user_id do JWT token

    Args:
        token: JWT token

    Returns:
        user_id ou None se inválido
    """
    payload = decode_token(token)
    if not payload:
        return None
    try:
        sub = payload.get("sub")
        if sub is None:
            return None
        return int(sub)
    except (TypeError, ValueError):
        return None


def require_valid_token_or_401(token: str) -> Dict[str, Any]:
    """
    Valida token e retorna payload ou lança exceção HTTP 401

    Args:
        token: JWT token

    Returns:
        Payload do token

    Raises:
        HTTPException: 401 se token inválido
    """
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload


def get_current_user_id(token: str) -> int:
    """
    Extrai e valida user_id do token ou lança exceção

    Args:
        token: JWT token

    Returns:
        user_id

    Raises:
        HTTPException: 401 se token inválido ou user_id não encontrado
    """
    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
