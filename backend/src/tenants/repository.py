"""
Repository para operações com inquilinos (tenants)
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from .models import Tenant
from .schema import TenantCreate, TenantUpdate, TenantCreateInternal


class TenantRepository:
    """Repository para operações com inquilinos"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, tenant_id: int) -> Optional[Tenant]:
        """Buscar inquilino por ID"""
        return self.db.query(Tenant).filter(Tenant.id == tenant_id).first()

    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Tenant]:
        """Buscar inquilinos do usuário"""
        return (
            self.db.query(Tenant)
            .filter(Tenant.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id_and_user(self, tenant_id: int, user_id: int) -> Optional[Tenant]:
        """Buscar inquilino por ID e usuário"""
        return (
            self.db.query(Tenant)
            .filter(Tenant.id == tenant_id, Tenant.user_id == user_id)
            .first()
        )

    def get_by_email(self, email: str, user_id: int) -> Optional[Tenant]:
        """Buscar inquilino por email"""
        return (
            self.db.query(Tenant)
            .filter(Tenant.email == email, Tenant.user_id == user_id)
            .first()
        )

    def get_by_cpf(self, cpf_cnpj: str, user_id: int) -> Optional[Tenant]:
        """Buscar inquilino por CPF/CNPJ"""
        return (
            self.db.query(Tenant)
            .filter(Tenant.cpf_cnpj == cpf_cnpj, Tenant.user_id == user_id)
            .first()
        )

    def create(self, tenant_data: TenantCreateInternal) -> Tenant:
        """Criar um novo inquilino"""
        db_tenant = Tenant(**tenant_data.dict())
        self.db.add(db_tenant)
        self.db.commit()
        self.db.refresh(db_tenant)
        return db_tenant

    def update(self, tenant_id: int, user_id: int, update_data: TenantUpdate) -> Optional[Tenant]:
        """Atualizar inquilino"""
        db_tenant = self.get_by_id_and_user(tenant_id, user_id)
        if not db_tenant:
            return None

        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(db_tenant, field, value)

        self.db.commit()
        self.db.refresh(db_tenant)
        return db_tenant

    def delete(self, tenant_id: int, user_id: int) -> bool:
        """Deletar inquilino"""
        db_tenant = self.get_by_id_and_user(tenant_id, user_id)
        if not db_tenant:
            return False

        self.db.delete(db_tenant)
        self.db.commit()
        return True

    def get_active_tenants(self, user_id: int) -> List[Tenant]:
        """Buscar inquilinos ativos"""
        return (
            self.db.query(Tenant)
            .filter(Tenant.user_id == user_id, Tenant.status == "active")
            .all()
        )

    def get_inactive_tenants(self, user_id: int) -> List[Tenant]:
        """Buscar inquilinos inativos"""
        return (
            self.db.query(Tenant)
            .filter(Tenant.user_id == user_id, Tenant.status == "inactive")
            .all()
        )

    def search_tenants(
        self,
        user_id: int,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Tenant]:
        """Buscar inquilinos por nome, email ou CPF"""
        return (
            self.db.query(Tenant)
            .filter(
                Tenant.user_id == user_id,
                (Tenant.name.ilike(f"%{search_term}%") |
                 Tenant.email.ilike(f"%{search_term}%") |
                 Tenant.cpf_cnpj.ilike(f"%{search_term}%"))
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_user(self, user_id: int) -> int:
        """Contar inquilinos do usuário"""
        return self.db.query(Tenant).filter(Tenant.user_id == user_id).count()

    def count_active_tenants(self, user_id: int) -> int:
        """Contar inquilinos ativos"""
        return (
            self.db.query(Tenant)
            .filter(Tenant.user_id == user_id, Tenant.status == "active")
            .count()
        )