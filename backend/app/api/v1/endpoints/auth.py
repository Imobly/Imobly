"""
Autenticação via Supabase
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.core.supabase_auth import get_supabase_client, get_current_user
from supabase import Client
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Modelos Pydantic
class LoginRequest(BaseModel):
    username: str = Field(..., description="Email ou username do usuário")
    password: str = Field(..., min_length=6, description="Senha do usuário")


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Email do usuário")
    username: str = Field(..., min_length=3, description="Nome de usuário")
    full_name: str = Field(..., min_length=3, description="Nome completo")
    password: str = Field(..., min_length=6, description="Senha")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., description="Senha atual")
    new_password: str = Field(..., min_length=6, description="Nova senha")


class UpdateUserRequest(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    refresh_token: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


@router.post("/login", response_model=TokenResponse, summary="Login do usuário")
async def login(
    credentials: LoginRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """
    Autentica usuário via Supabase Auth
    
    Aceita email ou username como identificador
    """
    try:
        # Tenta fazer login com email/password
        # Se username foi fornecido ao invés de email, tentamos com email
        email_or_username = credentials.username
        
        # Se não contém @, assume que é username e precisamos buscar o email
        if '@' not in email_or_username:
            # TODO: Implementar busca de email por username se necessário
            # Por enquanto, apenas tenta o login direto
            logger.warning(f"Username fornecido ao invés de email: {email_or_username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Por favor, use seu email para fazer login"
            )
        
        # Faz autenticação no Supabase
        response = supabase.auth.sign_in_with_password({
            "email": email_or_username,
            "password": credentials.password
        })
        
        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos"
            )
        
        return TokenResponse(
            access_token=response.session.access_token,
            token_type="Bearer",
            refresh_token=response.session.refresh_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao fazer login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )


@router.post("/register", response_model=UserResponse, summary="Registrar novo usuário")
async def register(
    user_data: RegisterRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """
    Registra um novo usuário no Supabase
    """
    try:
        # Cria usuário no Supabase Auth
        response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "full_name": user_data.full_name,
                    "username": user_data.username
                }
            }
        })
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao criar usuário. Email pode já estar em uso."
            )
        
        return UserResponse(
            id=response.user.id,
            email=response.user.email or user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            created_at=response.user.created_at.isoformat() if response.user.created_at else "",
            updated_at=response.user.updated_at.isoformat() if response.user.updated_at else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao registrar usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao registrar usuário: {str(e)}"
        )


@router.get("/me", response_model=UserResponse, summary="Obter usuário atual")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Retorna informações do usuário autenticado
    """
    return UserResponse(
        id=current_user.get("sub", ""),
        email=current_user.get("email", ""),
        username=current_user.get("user_metadata", {}).get("username"),
        full_name=current_user.get("user_metadata", {}).get("full_name"),
        created_at=current_user.get("created_at", ""),
        updated_at=current_user.get("updated_at", "")
    )


@router.post("/change-password", summary="Alterar senha")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Altera a senha do usuário autenticado
    """
    try:
        # Verifica a senha atual fazendo um novo login
        try:
            supabase.auth.sign_in_with_password({
                "email": current_user.get("email"),
                "password": password_data.current_password
            })
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Senha atual incorreta"
            )
        
        # Atualiza a senha
        response = supabase.auth.update_user({
            "password": password_data.new_password
        })
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao alterar senha"
            )
        
        return {"message": "Senha alterada com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao alterar senha: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao alterar senha"
        )


@router.put("/me", response_model=UserResponse, summary="Atualizar dados do usuário")
async def update_user(
    user_data: UpdateUserRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Atualiza informações do usuário autenticado
    """
    try:
        update_data = {}
        
        if user_data.email:
            update_data["email"] = user_data.email
        
        if user_data.full_name:
            update_data["data"] = {
                "full_name": user_data.full_name
            }
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhum dado para atualizar"
            )
        
        response = supabase.auth.update_user(update_data)
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao atualizar usuário"
            )
        
        return UserResponse(
            id=response.user.id,
            email=response.user.email or "",
            username=response.user.user_metadata.get("username"),
            full_name=response.user.user_metadata.get("full_name"),
            created_at=response.user.created_at.isoformat() if response.user.created_at else "",
            updated_at=response.user.updated_at.isoformat() if response.user.updated_at else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao atualizar usuário"
        )


@router.post("/logout", summary="Logout do usuário")
async def logout(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Faz logout do usuário (invalida token no Supabase)
    """
    try:
        supabase.auth.sign_out()
        return {"message": "Logout realizado com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao fazer logout: {str(e)}")
        # Mesmo com erro, retorna sucesso (logout local)
        return {"message": "Logout realizado com sucesso"}
