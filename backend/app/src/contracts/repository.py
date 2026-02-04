from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository

from .models import Contract
from .schemas import ContractCreate, ContractUpdate


class ContractRepository(BaseRepository[Contract, ContractCreate, ContractUpdate]):
    """Repository para operações com contratos"""

    def __init__(self, db: Session):
        super().__init__(Contract)
        self.db = db

    def get_by_user(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Contract]:
        """Buscar contratos do usuário"""
        return (
            db.query(Contract).filter(Contract.user_id == user_id).offset(skip).limit(limit).all()
        )

    def get_by_id_and_user(self, db: Session, contract_id: int, user_id: int) -> Optional[Contract]:
        """Buscar contrato por ID validando propriedade do usuário"""
        return (
            db.query(Contract)
            .filter(Contract.id == contract_id, Contract.user_id == user_id)
            .first()
        )

    def get_by_property(self, db: Session, property_id: int, user_id: int) -> List[Contract]:
        """Buscar contratos por propriedade"""
        return (
            db.query(Contract)
            .filter(Contract.property_id == property_id, Contract.user_id == user_id)
            .all()
        )

    def get_by_tenant(self, db: Session, tenant_id: int, user_id: int) -> List[Contract]:
        """Buscar contratos por inquilino"""
        return (
            db.query(Contract)
            .filter(Contract.tenant_id == tenant_id, Contract.user_id == user_id)
            .all()
        )

    def get_by_status(self, db: Session, status: str, user_id: int) -> List[Contract]:
        """Buscar contratos por status"""
        return (
            db.query(Contract).filter(Contract.status == status, Contract.user_id == user_id).all()
        )

    def get_active_contracts(self, db: Session, user_id: int) -> List[Contract]:
        """Buscar apenas contratos ativos"""
        return self.get_by_status(db, "active", user_id)

    def get_expiring_contracts(
        self, db: Session, user_id: int, days_ahead: int = 30
    ) -> List[Contract]:
        """Buscar contratos que vencem nos próximos X dias"""
        future_date = date.today() + timedelta(days=days_ahead)
        return (
            db.query(Contract)
            .filter(
                Contract.user_id == user_id,
                Contract.status == "active",
                Contract.end_date <= future_date,
                Contract.end_date >= date.today(),
            )
            .all()
        )

    def get_expired_contracts(self, db: Session, user_id: int) -> List[Contract]:
        """Buscar contratos vencidos"""
        return (
            db.query(Contract)
            .filter(
                Contract.user_id == user_id,
                Contract.end_date < date.today(),
                Contract.status == "active",
            )
            .all()
        )

    def get_current_contract_for_property(
        self, db: Session, property_id: int, user_id: int
    ) -> Optional[Contract]:
        """Buscar contrato ativo atual de uma propriedade"""
        return (
            db.query(Contract)
            .filter(
                Contract.property_id == property_id,
                Contract.user_id == user_id,
                Contract.status == "active",
                Contract.start_date <= date.today(),
                Contract.end_date >= date.today(),
            )
            .first()
        )

    def get_current_contract_for_tenant(
        self, db: Session, tenant_id: int, user_id: int
    ) -> Optional[Contract]:
        """Buscar contrato ativo atual de um inquilino"""
        return (
            db.query(Contract)
            .filter(
                Contract.tenant_id == tenant_id,
                Contract.user_id == user_id,
                Contract.status == "active",
                Contract.start_date <= date.today(),
                Contract.end_date >= date.today(),
            )
            .first()
        )

    def check_property_availability(
        self,
        db: Session,
        property_id: int,
        user_id: int,
        start_date: date,
        end_date: date,
        exclude_contract_id: Optional[int] = None,
    ) -> bool:
        """Verificar se propriedade está disponível no período
        
        Uma propriedade está disponível se:
        1. Não há contratos ativos que se sobrepõem ao período
        2. OU o contrato ativo já expirou (end_date < hoje)
        """
        query = db.query(Contract).filter(
            Contract.property_id == property_id,
            Contract.user_id == user_id,
            Contract.status == "active",
            Contract.end_date >= date.today(),  # Apenas contratos que ainda não expiraram
            or_(
                and_(Contract.start_date <= start_date, Contract.end_date >= start_date),
                and_(Contract.start_date <= end_date, Contract.end_date >= end_date),
                and_(Contract.start_date >= start_date, Contract.end_date <= end_date),
            ),
        )

        if exclude_contract_id:
            query = query.filter(Contract.id != exclude_contract_id)

        return query.first() is None

    def get_by_title(self, db: Session, user_id: int, title: str) -> Optional[Contract]:
        """Buscar contrato por título (filtrando por usuário)"""
        return db.query(Contract).filter(
            Contract.user_id == user_id,
            Contract.title == title
        ).first()

    def check_unique_title(
        self, db: Session, user_id: int, title: str, exclude_contract_id: Optional[int] = None
    ) -> bool:
        """Verificar se título do contrato é único (no escopo do usuário)"""
        query = db.query(Contract).filter(
            Contract.user_id == user_id,
            Contract.title == title
        )
        if exclude_contract_id:
            query = query.filter(Contract.id != exclude_contract_id)
        
        return query.first() is None

    def update_status(
        self, db: Session, contract_id: int, user_id: int, status: str
    ) -> Optional[Contract]:
        """Atualizar apenas o status do contrato"""
        contract_obj = self.get_by_id_and_user(db, contract_id, user_id)
        if contract_obj:
            contract_obj.status = status
            db.commit()
            db.refresh(contract_obj)
            return contract_obj
        return None

    def renew_contract(
        self,
        db: Session,
        contract_id: int,
        user_id: int,
        new_end_date: date,
        new_rent: Optional[float] = None,
    ) -> Optional[Contract]:
        """Renovar contrato"""
        contract_obj = self.get_by_id_and_user(db, contract_id, user_id)
        if contract_obj:
            contract_obj.end_date = new_end_date
            if new_rent:
                contract_obj.rent = new_rent
            db.commit()
            db.refresh(contract_obj)
            return contract_obj
        return None
