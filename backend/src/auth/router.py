"""
Endpoints de autenticação
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends
from sqlalchemy.orm import Session
from supabase import Client
import logging

from src.core.rate_limit import (
    LIMITE_LOGIN,
    LIMITE_REGISTRO,
    LIMITE_TROCA_SENHA,
    limiter,
)
from src.database import get_db
from src.security import get_supabase_client, get_current_user
from src.auth.repository import AuthRepository
from src.auth.schema import (
    LoginRequest,
    RefreshRequest,
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
@limiter.limit(LIMITE_LOGIN)
async def login(
    request: Request,
    credentials: LoginRequest,
    auth_repo: AuthRepository = Depends(get_auth_repository)
):
    """
    Autentica usuário via Supabase Auth

    Aceita email ou username como identificador
    """
    email_or_username = credentials.username

    # Compõe a chave do rate limit com o identificador, não só o IP: sem isso
    # um atacante atrás de IP rotativo varre contas sem esbarrar no limite.
    request.state.rate_limit_identity = email_or_username.lower()

    # Se não contém @, é username - buscar email na tabela local
    if '@' not in email_or_username:
        email = auth_repo.get_email_by_username(email_or_username)
        if not email:
            # Mensagem genérica para não permitir enumeração de usuários.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos"
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


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Registrar novo usuário")
@limiter.limit(LIMITE_REGISTRO)
async def register(
    request: Request,
    user_data: RegisterRequest,
    auth_repo: AuthRepository = Depends(get_auth_repository)
):
    """
    Registra um novo usuário no Supabase
    """
    request.state.rate_limit_identity = user_data.email.lower()
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


def _user_response(current_user: dict, auth_repo: AuthRepository) -> UserResponse:
    """Monta o UserResponse combinando o token com o registro local."""
    email = current_user.get("email") or ""
    # Resolve pela chave imutável; e-mail só como fallback para linhas legadas
    # ainda sem supabase_uid preenchido.
    local_user = auth_repo.get_local_user_by_uid(current_user["id"])
    if local_user is None and email:
        local_user = auth_repo.get_local_user_by_email(email)
    return UserResponse(
        id=str(local_user.id) if local_user else current_user["id"],
        email=local_user.email if local_user else email,
        username=local_user.username if local_user else None,
        full_name=local_user.full_name if local_user else None,
        created_at=local_user.created_at.isoformat() if local_user and local_user.created_at else "",
        updated_at=local_user.updated_at.isoformat() if local_user and local_user.updated_at else None,
    )


@router.get("/me", response_model=UserResponse, summary="Obter dados do usuário atual")
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    auth_repo: AuthRepository = Depends(get_auth_repository),
):
    """
    Retorna informações do usuário autenticado atual (a partir da tabela local).
    """
    return _user_response(current_user, auth_repo)


@router.put("/me", response_model=UserResponse, summary="Atualizar dados do usuário atual")
async def update_current_user_profile(
    user_data: UpdateUserRequest,
    current_user: dict = Depends(get_current_user),
    auth_repo: AuthRepository = Depends(get_auth_repository),
):
    """
    Atualiza o nome completo do usuário na tabela local.

    A troca de e-mail NÃO é aceita aqui: o e-mail é credencial de autenticação,
    e alterá-lo somente na tabela local dessincroniza a conta do Supabase.
    """
    email = current_user.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email não encontrado no token",
        )

    if user_data.email is not None and user_data.email.lower() != email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A alteração de e-mail não é feita por esta rota — ela exige "
                "verificação de posse do novo endereço."
            ),
        )

    updated = auth_repo.update_local_user(
        supabase_uid=current_user["id"],
        full_name=user_data.full_name,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    return UserResponse(
        id=str(updated.id),
        email=updated.email,
        username=updated.username,
        full_name=updated.full_name,
        created_at=updated.created_at.isoformat() if updated.created_at else "",
        updated_at=updated.updated_at.isoformat() if updated.updated_at else None,
    )


@router.post("/change-password", summary="Alterar senha")
@limiter.limit(LIMITE_TROCA_SENHA)
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    auth_repo: AuthRepository = Depends(get_auth_repository)
):
    """
    Altera a senha do usuário autenticado, validando a senha atual.

    A rota reautentica para validar a senha atual, o que a torna um oráculo
    de senha — daí o limite, apesar de já exigir token válido.
    """
    request.state.rate_limit_identity = current_user["id"]
    await auth_repo.change_password(
        supabase_user_id=current_user["id"],
        email=current_user["email"],
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )

    return {"message": "Senha alterada com sucesso"}


@router.post("/logout", summary="Logout")
async def logout():
    """
    Endpoint de logout (client-side apenas)
    """
    return {"message": "Logout realizado com sucesso"}


@router.post("/refresh", response_model=TokenResponse, summary="Renovar token")
@limiter.limit(LIMITE_LOGIN)
async def refresh_token(
    request: Request,
    data: RefreshRequest,
    auth_repo: AuthRepository = Depends(get_auth_repository),
):
    """
    Renova o par de tokens a partir do refresh token.

    O access token do Supabase expira em ~1h. Sem esta rota, o frontend
    derrubava o usuário para /login no meio do trabalho.
    """
    result = await auth_repo.refresh_session(data.refresh_token)

    return TokenResponse(
        access_token=result["access_token"],
        token_type=result["token_type"],
        refresh_token=result.get("refresh_token"),
    )
