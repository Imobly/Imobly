from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository

from .models import Tenant
from .schemas import TenantCreate, TenantUpdate


class TenantRepository(BaseRepository[Tenant, TenantCreate, TenantUpdate]):
    """Repository para operações com inquilinos"""

    def __init__(self, db: Session):
        super().__init__(Tenant)
        self.db = db

    def get_by_user(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Tenant]:
        """Buscar inquilinos do usuário"""
        return db.query(Tenant).filter(Tenant.user_id == user_id).offset(skip).limit(limit).all()

    def get_by_id_and_user(self, db: Session, tenant_id: int, user_id: int) -> Optional[Tenant]:
        """Buscar inquilino por ID validando owner"""
        return db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.user_id == user_id).first()

    def get_by_email(self, db: Session, user_id: int, email: str) -> Optional[Tenant]:
        """Buscar inquilino por email (filtrando por usuário)"""
        return db.query(Tenant).filter(Tenant.user_id == user_id, Tenant.email == email).first()

    def get_by_cpf(self, db: Session, user_id: int, cpf: str) -> Optional[Tenant]:
        """Buscar inquilino por CPF (filtrando por usuário)"""
        return db.query(Tenant).filter(Tenant.user_id == user_id, Tenant.cpf_cnpj == cpf).first()

    def get_by_phone(self, db: Session, user_id: int, phone: str) -> Optional[Tenant]:
        """Buscar inquilino por telefone (filtrando por usuário)"""
        return db.query(Tenant).filter(Tenant.user_id == user_id, Tenant.phone == phone).first()

    def search_tenants(
        self,
        db: Session,
        user_id: int,
        *,
        name: Optional[str] = None,
        email: Optional[str] = None,
        cpf: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Tenant]:
        """Buscar inquilinos com filtros (filtrando por usuário)"""
        query = db.query(Tenant).filter(Tenant.user_id == user_id)

        if name:
            query = query.filter(Tenant.name.ilike(f"%{name}%"))

        if email:
            query = query.filter(Tenant.email.ilike(f"%{email}%"))

        if cpf:
            # Search by CPF/CNPJ column
            query = query.filter(Tenant.cpf_cnpj == cpf)

        return query.offset(skip).limit(limit).all()

    def check_unique_constraints(
        self, db: Session, user_id: int, tenant_data: TenantCreate, exclude_id: Optional[int] = None
    ) -> dict:
        """Verificar se email e CPF são únicos (no escopo do usuário)"""
        errors = {}

        # Verificar email único (no escopo do usuário)
        email_query = db.query(Tenant).filter(
            Tenant.user_id == user_id, Tenant.email == tenant_data.email
        )
        if exclude_id:
            email_query = email_query.filter(Tenant.id != exclude_id)

        if email_query.first():
            errors["email"] = "Email já está em uso"

        # Verificar CPF único (no escopo do usuário)
        cpf_query = db.query(Tenant).filter(
            Tenant.user_id == user_id, Tenant.cpf_cnpj == tenant_data.cpf_cnpj
        )
        if exclude_id:
            cpf_query = cpf_query.filter(Tenant.id != exclude_id)

        if cpf_query.first():
            errors["cpf_cnpj"] = "CPF/CNPJ já está em uso"

        return errors
