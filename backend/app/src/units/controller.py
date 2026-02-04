from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .repository import UnitRepository
from .schemas import Unit, UnitCreate, UnitUpdate


class unit_controller:
    """Controller para gerenciar operações de unidades"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = UnitRepository(db)

    def get_units(self, db: Session, skip: int = 0, limit: int = 100) -> List[Unit]:
        """Listar unidades"""
        return self.repository.get_multi(db, skip=skip, limit=limit)

    def get_units_by_property(self, db: Session, property_id: int) -> List[Unit]:
        """Obter unidades por propriedade"""
        return self.repository.get_by_property(db, property_id=property_id)

    def get_unit_by_id(self, db: Session, unit_id: int) -> Unit:
        """Obter unidade por ID"""
        unit_obj = self.repository.get(db, unit_id)
        if not unit_obj:
            raise HTTPException(status_code=404, detail="Unidade não encontrada")
        return unit_obj

    def create_unit(self, db: Session, unit_data: UnitCreate) -> Unit:
        """Criar nova unidade"""
        return self.repository.create(db, obj_in=unit_data)

    def update_unit(self, db: Session, unit_id: int, unit_data: UnitUpdate) -> Unit:
        """Atualizar unidade existente"""
        unit_obj = self.repository.get(db, unit_id)
        if not unit_obj:
            raise HTTPException(status_code=404, detail="Unidade não encontrada")

        return self.repository.update(db, db_obj=unit_obj, obj_in=unit_data)

    def delete_unit(self, db: Session, unit_id: int) -> dict:
        """Deletar unidade"""
        success = self.repository.delete(db, id=unit_id)
        if not success:
            raise HTTPException(status_code=404, detail="Unidade não encontrada")
        return {"message": "Unidade deletada com sucesso"}

    def get_available_units(self, db: Session) -> List[Unit]:
        """Obter apenas unidades disponíveis"""
        return self.repository.get_available_units(db)


# Instância global do controller
