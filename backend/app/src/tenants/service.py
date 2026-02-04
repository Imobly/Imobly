from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from .models import Tenant
from .schemas import TenantCreate, TenantUpdate


def get_tenant(db: Session, tenant_id: int) -> Optional[Tenant]:
    """Obter inquilino por ID"""
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()


def get_tenants(db: Session, skip: int = 0, limit: int = 100) -> List[Tenant]:
    """Listar inquilinos com paginação"""
    return db.query(Tenant).offset(skip).limit(limit).all()


def create_tenant(db: Session, tenant: TenantCreate) -> Tenant:
    """Criar novo inquilino"""
    db_tenant = Tenant(**tenant.dict())
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant


def update_tenant(db: Session, tenant_id: int, tenant: TenantUpdate) -> Optional[Tenant]:
    """Atualizar inquilino existente"""
    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if db_tenant:
        update_data = tenant.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_tenant, field, value)
        db_tenant.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_tenant)
    return db_tenant


def delete_tenant(db: Session, tenant_id: int) -> bool:
    """Deletar inquilino"""
    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if db_tenant:
        db.delete(db_tenant)
        db.commit()
        return True
    return False
