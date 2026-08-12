"""
Repository para autenticação
Lógica de interação com Supabase Auth e tabela users
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from supabase import Client
from sqlalchemy.exc import IntegrityError
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
        
        # Busca pela chave imutável; e-mail apenas como fallback legado
        user = self.db.query(User).filter(User.supabase_uid == supabase_user_id).first()

        if not user:
            legacy = self.db.query(User).filter(User.email == email).first()
            if legacy is not None and not legacy.supabase_uid:
                legacy.supabase_uid = supabase_user_id
                self.db.commit()
                self.db.refresh(legacy)
                user = legacy
            elif legacy is not None:
                user = legacy

        if not user:
            # Cria novo usuário
            user = User(
                supabase_uid=supabase_user_id,
                email=email,
                username=username,
                full_name=full_name or username,
                hashed_password=supabase_user_id,  # Armazena o UUID do Supabase como referência
                is_active=True,
                is_superuser=False
            )
            self.db.add(user)
            try:
                self.db.commit()
                self.db.refresh(user)
            except IntegrityError:
                # Corrida com outra requisição do mesmo usuário — releia a linha vencedora.
                self.db.rollback()
                user = self.db.query(User).filter(User.supabase_uid == supabase_user_id).first()
                if user is None:
                    raise
            else:
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
            # Não vazar o detalhe interno ao cliente; apenas registrar no log.
            logger.error(f"Erro ao registrar usuário: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível registrar o usuário. Verifique os dados ou tente outro email."
            )
    
    async def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """
        Troca o refresh token por um novo par de tokens no Supabase.

        Sem isso o usuário era deslogado toda vez que o access token expirava
        (1h por padrão) — no meio do trabalho, perdendo formulários abertos.

        Raises:
            HTTPException 401: refresh token inválido, expirado ou já usado.
        """
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            if not response or not response.session:
                raise ValueError("sessão não retornada")
        except HTTPException:
            raise
        except Exception as e:
            # Não distinga "expirado" de "inválido": a diferença só serve para
            # quem está sondando tokens.
            logger.info(f"Falha ao renovar sessão: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sessão expirada. Faça login novamente.",
            )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "Bearer",
        }

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
    
    def get_local_user_by_email(self, email: str) -> Optional[User]:
        """Busca o registro local do usuário por email"""
        if not self.db:
            return None
        return self.db.query(User).filter(User.email == email).first()

    def get_local_user_by_uid(self, supabase_uid: str) -> Optional[User]:
        """
        Busca o registro local pela chave de identidade imutável.

        Preferível a `get_local_user_by_email`: o e-mail muda, o uid não.
        """
        if not self.db:
            return None
        return self.db.query(User).filter(User.supabase_uid == supabase_uid).first()

    def update_local_user(self, supabase_uid: str, full_name: Optional[str] = None) -> Optional[User]:
        """
        Atualiza campos editáveis do usuário na tabela local.

        Só `full_name` é editável por aqui. A troca de e-mail foi removida de
        propósito: o e-mail é dado de autenticação e alterá-lo apenas na tabela
        local dessincronizava a conta do Supabase. Ela precisa passar pelo fluxo
        de verificação de posse do novo endereço.

        Returns:
            User atualizado, ou None se não encontrado.
        """
        if not self.db:
            raise Exception("Database session não configurada no AuthRepository")

        user = self.db.query(User).filter(User.supabase_uid == supabase_uid).first()
        if not user:
            return None

        if full_name is not None:
            user.full_name = full_name

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(user)
        return user

    async def change_password(self, supabase_user_id: str, email: str, current_password: str, new_password: str) -> bool:
        """
        Altera a senha do usuário, validando a senha atual antes.

        - Valida a senha atual reautenticando no Supabase.
        - Aplica a nova senha via Admin API (cliente usa SERVICE_ROLE_KEY).

        Raises:
            HTTPException 400: se a senha atual estiver incorreta.
        """
        # 1. Validar senha atual
        try:
            auth_check = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": current_password,
            })
            if not auth_check.user:
                raise ValueError("invalid current password")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Senha atual incorreta",
            )

        # 2. Aplicar nova senha (Admin API — não depende da sessão do usuário)
        try:
            self.supabase.auth.admin.update_user_by_id(
                supabase_user_id, {"password": new_password}
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar senha: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível alterar a senha. Tente novamente.",
            )
