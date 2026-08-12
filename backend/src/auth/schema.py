"""
Schemas para autenticação
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


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


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="Refresh token do Supabase")


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