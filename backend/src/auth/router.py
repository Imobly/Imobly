"""
Endpoints de autenticação
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from supabase import Client
import logging

from src.database import get_db
from src.security import get_supabase_client, get_current_user
from src.auth.repository import AuthRepository
from src.auth.schema import (
    LoginRequest, 
    RegisterRequest, 
    TokenResponse, 
    UserResponse,
    ChangePasswordRequest,
    UpdateUserRequest
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_auth_repository(
    supabase: Client = Depends(get_supabase_client),
    db: Session = Depends(get_db)
) -> AuthRepository:
    """Dependency para obter repository de autenticação"""
    return AuthRepository(supabase, db)


@router.post("/login", response_model=TokenResponse, summary="Login do usuário")
async def login(
    credentials: LoginRequest,
    auth_repo: AuthRepository = Depends(get_auth_repository)
):
    """
    Autentica usuário via Supabase Auth
    
    Aceita email ou username como identificador
    """
    email_or_username = credentials.username
    
    # Se não contém @, é username - buscar email na tabela local
    if '@' not in email_or_username:
        email = auth_repo.get_email_by_username(email_or_username)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
    else:
        email = email_or_username
    
    # Autentica usuário
    result = await auth_repo.authenticate_user(email, credentials.password)
    
    return TokenResponse(
        access_token=result["access_token"],
        token_type=result["token_type"],
        refresh_token=result.get("refresh_token")
    )


@router.post("/register", response_model=UserResponse, summary="Registrar novo usuário")
async def register(
    user_data: RegisterRequest,
    auth_repo: AuthRepository = Depends(get_auth_repository)
):
    """
    Registra um novo usuário no Supabase
    """
    result = await auth_repo.create_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        username=user_data.username
    )
    
    user = result["user"]
    
    return UserResponse(
        id=user.id,
        email=user.email or user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        created_at=user.created_at.isoformat() if user.created_at else "",
        updated_at=user.updated_at.isoformat() if user.updated_at else ""
    )


@router.get("/me", response_model=UserResponse, summary="Obter dados do usuário atual")
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Retorna informações do usuário autenticado atual
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        username=current_user.get("username"),
        full_name=current_user.get("full_name"),
        created_at=current_user.get("created_at", ""),
        updated_at=current_user.get("updated_at")
    )


@router.post("/change-password", summary="Alterar senha")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    auth_repo: AuthRepository = Depends(get_auth_repository)
):
    """
    Altera a senha do usuário autenticado
    """
    # Note: Implementação simplificada - em produção, deve validar senha atual
    success = await auth_repo.update_password(
        access_token=current_user["access_token"],  # Precisa passar o token
        new_password=password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao alterar senha"
        )
    
    return {"message": "Senha alterada com sucesso"}


@router.post("/logout", summary="Logout")
async def logout():
    """
    Endpoint de logout (client-side apenas)
    """
    return {"message": "Logout realizado com sucesso"}


@router.post("/refresh", summary="Renovar token")
async def refresh_token():
    """
    Renova o token de acesso (implementação futura)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Renovação de token não implementada"
    )
