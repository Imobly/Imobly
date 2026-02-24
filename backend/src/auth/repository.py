"""
Repository para autenticação
Lógica de interação com Supabase Auth e tabela users
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from supabase import Client
from sqlalchemy.orm import Session
import logging

from src.auth.models import User

logger = logging.getLogger(__name__)


class AuthRepository:
    """Repository para operações de autenticação via Supabase"""
    
    def __init__(self, supabase_client: Client, db: Optional[Session] = None):
        self.supabase = supabase_client
        self.db = db
    
    def get_email_by_username(self, username: str) -> Optional[str]:
        """
        Busca email do usuário pelo username na tabela local
        
        Args:
            username: Nome de usuário
            
        Returns:
            str: Email do usuário ou None se não encontrado
        """
        if not self.db:
            return None
            
        user = self.db.query(User).filter(User.username == username).first()
        return user.email if user else None
    
    def get_or_create_local_user(self, supabase_user_id: str, email: str, username: str, full_name: str = None) -> User:
        """
        Busca ou cria usuário na tabela local users
        
        Args:
            supabase_user_id: UUID do usuário no Supabase
            email: Email do usuário
            username: Username
            full_name: Nome completo
            
        Returns:
            User: Registro do usuário na tabela local
        """
        if not self.db:
            raise Exception("Database session não configurada no AuthRepository")
        
        # Busca usuário por email
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            # Cria novo usuário
            user = User(
                email=email,
                username=username,
                full_name=full_name or username,
                hashed_password=supabase_user_id,  # Armazena o UUID do Supabase como referência
                is_active=True,
                is_superuser=False
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Usuário local criado: {email} (id={user.id})")
        
        return user
    
    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Autentica usuário no Supabase e sincroniza com tabela local
        
        Args:
            email: Email do usuário
            password: Senha do usuário
            
        Returns:
            Dict contendo access_token, refresh_token, dados do usuário e local_user_id
            
        Raises:
            HTTPException: Se credenciais inválidas
        """
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not response.user or not response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email ou senha incorretos"
                )
            
            # Sincroniza usuário com tabela local
            local_user = None
            if self.db:
                user_metadata = response.user.user_metadata or {}
                username = user_metadata.get("username", email.split("@")[0])
                full_name = user_metadata.get("full_name", username)
                
                local_user = self.get_or_create_local_user(
                    supabase_user_id=response.user.id,
                    email=email,
                    username=username,
                    full_name=full_name
                )
            
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "token_type": "Bearer",
                "user": response.user,
                "local_user_id": local_user.id if local_user else None
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao fazer login: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos"
            )
    
    async def create_user(self, email: str, password: str, full_name: str, username: str) -> Dict[str, Any]:
        """
        Cria novo usuário no Supabase e na tabela local
        
        Args:
            email: Email do usuário
            password: Senha do usuário
            full_name: Nome completo
            username: Username
            
        Returns:
            Dict com dados do usuário criado e local_user_id
            
        Raises:
            HTTPException: Se erro na criação
        """
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "username": username
                    }
                }
            })
            
            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Erro ao criar usuário. Email pode já estar em uso."
                )
            
            # Cria usuário na tabela local
            local_user = None
            if self.db:
                local_user = self.get_or_create_local_user(
                    supabase_user_id=response.user.id,
                    email=email,
                    username=username,
                    full_name=full_name
                )
            
            return {
                "user": response.user,
                "session": response.session,
                "local_user_id": local_user.id if local_user else None
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao registrar usuário: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erro ao registrar usuário: {str(e)}"
            )
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca usuário por ID
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dict com dados do usuário ou None
        """
        try:
            response = self.supabase.auth.admin.get_user_by_id(user_id)
            return response.user.__dict__ if response.user else None
        except Exception as e:
            logger.error(f"Erro ao buscar usuário: {str(e)}")
            return None
    
    async def update_password(self, access_token: str, new_password: str) -> bool:
        """
        Atualiza senha do usuário
        
        Args:
            access_token: Token de acesso do usuário
            new_password: Nova senha
            
        Returns:
            bool: True se sucesso
        """
        try:
            # Autentica com o token
            self.supabase.auth.set_session(access_token, "")
            
            response = self.supabase.auth.update_user({
                "password": new_password
            })
            
            return response.user is not None
            
        except Exception as e:
            logger.error(f"Erro ao atualizar senha: {str(e)}")
            return False