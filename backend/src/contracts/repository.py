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
        """
        Contratos ativos que vencem nos próximos `days_ahead` dias.

        O piso (`end_date >= hoje`) faltava: contratos ativos JÁ vencidos —
        enquanto o job diário não roda e os marca como expirados — apareciam
        como "vencendo em 30 dias".
        """
        from datetime import timedelta

        from src.core.tempo import hoje_brt

        hoje = hoje_brt()
        cutoff = hoje + timedelta(days=days_ahead)
        return (
            self.db.query(Contract)
            .filter(
                Contract.user_id == user_id,
                Contract.status == "ativo",
                Contract.end_date >= hoje,
                Contract.end_date <= cutoff,
            )
            .order_by(Contract.end_date.asc())
            .all()
        )

    def create(self, data: ContractCreateInternal, commit: bool = True) -> Contract:
        """
        `commit=False` quando a rota precisa gravar contrato e imóvel na MESMA
        transação — do contrário uma falha entre os dois commits deixa um
        contrato ativo com o imóvel marcado como vago.
        """
        contract = Contract(**data.model_dump())
        self.db.add(contract)
        if commit:
            self.db.commit()
            self.db.refresh(contract)
        else:
            self.db.flush()
        return contract

    def update(self, contract_id: int, user_id: int, data: ContractUpdate) -> Optional[Contract]:
        contract = self.get_by_id_and_user(contract_id, user_id)
        if not contract:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contract, field, value)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def update_status(
        self, contract_id: int, user_id: int, new_status: str, commit: bool = True
    ) -> Optional[Contract]:
        contract = self.get_by_id_and_user(contract_id, user_id)
        if not contract:
            return None
        contract.status = new_status
        if commit:
            self.db.commit()
            self.db.refresh(contract)
        else:
            self.db.flush()
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

    def delete(self, contract_id: int, user_id: int, commit: bool = True) -> bool:
        contract = self.get_by_id_and_user(contract_id, user_id)
        if not contract:
            return False
        self.db.delete(contract)
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        return True
