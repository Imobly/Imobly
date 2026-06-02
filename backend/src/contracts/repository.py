"""
Repository para operações CRUD de contratos
"""

from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from .models import Contract
from .schema import ContractCreateInternal, ContractUpdate


class ContractRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Contract]:
        return (
            self.db.query(Contract)
            .filter(Contract.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id_and_user(self, contract_id: int, user_id: int) -> Optional[Contract]:
        return (
            self.db.query(Contract)
            .filter(Contract.id == contract_id, Contract.user_id == user_id)
            .first()
        )

    def get_by_id(self, contract_id: int) -> Optional[Contract]:
        return self.db.query(Contract).filter(Contract.id == contract_id).first()

    def get_by_tenant(self, tenant_id: int, user_id: int) -> List[Contract]:
        return (
            self.db.query(Contract)
            .filter(Contract.tenant_id == tenant_id, Contract.user_id == user_id)
            .all()
        )

    def get_by_property(self, property_id: int, user_id: int) -> List[Contract]:
        return (
            self.db.query(Contract)
            .filter(Contract.property_id == property_id, Contract.user_id == user_id)
            .all()
        )

    def get_active(self, user_id: int) -> List[Contract]:
        return (
            self.db.query(Contract)
            .filter(Contract.user_id == user_id, Contract.status == "ativo")
            .all()
        )

    def get_by_status(self, user_id: int, status: str) -> List[Contract]:
        return (
            self.db.query(Contract)
            .filter(Contract.user_id == user_id, Contract.status == status)
            .all()
        )

    def get_expiring(self, user_id: int, days_ahead: int = 30) -> List[Contract]:
        from datetime import timedelta
        cutoff = date.today() + timedelta(days=days_ahead)
        return (
            self.db.query(Contract)
            .filter(
                Contract.user_id == user_id,
                Contract.status == "ativo",
                Contract.end_date <= cutoff,
            )
            .all()
        )

    def create(self, data: ContractCreateInternal) -> Contract:
        contract = Contract(**data.dict())
        self.db.add(contract)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def update(self, contract_id: int, user_id: int, data: ContractUpdate) -> Optional[Contract]:
        contract = self.get_by_id_and_user(contract_id, user_id)
        if not contract:
            return None
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contract, field, value)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def update_status(self, contract_id: int, user_id: int, new_status: str) -> Optional[Contract]:
        contract = self.get_by_id_and_user(contract_id, user_id)
        if not contract:
            return None
        contract.status = new_status
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def renew(self, contract_id: int, user_id: int, new_end_date: date, new_rent: Optional[float] = None) -> Optional[Contract]:
        contract = self.get_by_id_and_user(contract_id, user_id)
        if not contract:
            return None
        contract.end_date = new_end_date
        contract.status = "ativo"
        if new_rent is not None:
            contract.rent = new_rent
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def delete(self, contract_id: int, user_id: int) -> bool:
        contract = self.get_by_id_and_user(contract_id, user_id)
        if not contract:
            return False
        self.db.delete(contract)
        self.db.commit()
        return True
