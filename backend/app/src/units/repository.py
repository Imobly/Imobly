from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository

from .models import Unit
from .schemas import UnitCreate, UnitUpdate


class UnitRepository(BaseRepository[Unit, UnitCreate, UnitUpdate]):
    """Repository para operações com unidades"""

    def __init__(self, db: Session):
        super().__init__(Unit)
        self.db = db

    def get_by_property(self, db: Session, property_id: int) -> List[Unit]:
        """Buscar unidades por propriedade"""
        return db.query(Unit).filter(Unit.property_id == property_id).all()

    def get_by_status(self, db: Session, status: str) -> List[Unit]:
        """Buscar unidades por status"""
        return db.query(Unit).filter(Unit.status == status).all()

    def get_by_property_and_status(self, db: Session, property_id: int, status: str) -> List[Unit]:
        """Buscar unidades por propriedade e status"""
        return db.query(Unit).filter(Unit.property_id == property_id, Unit.status == status).all()

    def get_by_number(self, db: Session, property_id: int, number: str) -> Optional[Unit]:
        """Buscar unidade por número dentro de uma propriedade"""
        return db.query(Unit).filter(Unit.property_id == property_id, Unit.number == number).first()

    def update_status(self, db: Session, unit_id: int, status: str) -> Optional[Unit]:
        """Atualizar apenas o status da unidade"""
        unit_obj = self.get(db, unit_id)
        if unit_obj:
            unit_obj.status = status
            db.commit()
            db.refresh(unit_obj)
            return unit_obj
        return None

    def assign_tenant(self, db: Session, unit_id: int, tenant_name: str) -> Optional[Unit]:
        """Atribuir inquilino à unidade"""
        unit_obj = self.get(db, unit_id)
        if unit_obj:
            unit_obj.tenant = tenant_name
            unit_obj.status = "occupied"
            db.commit()
            db.refresh(unit_obj)
            return unit_obj
        return None

    def remove_tenant(self, db: Session, unit_id: int) -> Optional[Unit]:
        """Remover inquilino da unidade"""
        unit_obj = self.get(db, unit_id)
        if unit_obj:
            unit_obj.tenant = None
            unit_obj.status = "vacant"
            db.commit()
            db.refresh(unit_obj)
            return unit_obj
        return None
