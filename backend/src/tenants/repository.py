"""
Repository para operações com inquilinos (tenants)
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from .models import Tenant
from .schema import TenantCreate, TenantUpdate, TenantCreateInternal
from src.contracts.models import Contract


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
        """
        Buscar inquilino por email (case-insensitive).

        A comparação precisa bater com o índice único `ux_tenants_user_email`,
        que é sobre `lower(email)` — senão a checagem passa e o INSERT estoura.
        """
        from sqlalchemy import func

        return (
            self.db.query(Tenant)
            .filter(
                func.lower(Tenant.email) == (email or "").lower(),
                Tenant.user_id == user_id,
            )
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
        """Buscar inquilinos ativos (com contrato ativo)"""
        from sqlalchemy import and_
        return (
            self.db.query(Tenant)
            .join(
                Contract,
                and_(Tenant.contract_id == Contract.id, Contract.user_id == user_id),
            )
            .filter(Tenant.user_id == user_id, Contract.status == "ativo")
            .all()
        )

    def get_inactive_tenants(self, user_id: int) -> List[Tenant]:
        """Buscar inquilinos inativos (sem contrato ativo)"""
        from sqlalchemy import and_, or_
        return (
            self.db.query(Tenant)
            .outerjoin(
                Contract,
                and_(Tenant.contract_id == Contract.id, Contract.user_id == user_id),
            )
            .filter(
                Tenant.user_id == user_id,
                or_(Tenant.contract_id.is_(None), Contract.status != "ativo"),
            )
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

    def anexar_status(self, tenants: List[Tenant], user_id: int) -> List[Tenant]:
        """
        Preenche o atributo `status` de cada inquilino a partir do contrato.

        O status não é coluna — deriva do contrato vinculado. Resolvido em UMA
        query para a lista inteira, em vez de uma por inquilino.
        """
        if not tenants:
            return tenants

        ids_de_contrato = {t.contract_id for t in tenants if t.contract_id}
        ativos: set = set()
        if ids_de_contrato:
            ativos = {
                cid
                for (cid,) in self.db.query(Contract.id)
                .filter(
                    Contract.id.in_(ids_de_contrato),
                    Contract.user_id == user_id,
                    Contract.status == "ativo",
                )
                .all()
            }

        for tenant in tenants:
            tenant.status = "ativo" if tenant.contract_id in ativos else "inativo"
        return tenants

    def count_by_user(self, user_id: int) -> int:
        """Contar inquilinos do usuário"""
        return self.db.query(Tenant).filter(Tenant.user_id == user_id).count()

    def count_active_tenants(self, user_id: int) -> int:
        """Contar inquilinos ativos (com contrato ativo)"""
        from sqlalchemy import and_
        return (
            self.db.query(Tenant)
            .join(
                Contract,
                and_(Tenant.contract_id == Contract.id, Contract.user_id == user_id),
            )
            .filter(Tenant.user_id == user_id, Contract.status == "ativo")
            .count()
        )