from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from .controller import unit_controller
from .schemas import UnitCreate, UnitResponse, UnitUpdate

router = APIRouter()


@router.post("/", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
async def create_unit(unit: UnitCreate, db: Session = Depends(get_db)):
    """Criar nova unidade"""
    return unit_controller(db).create_unit(db, unit)


@router.get("/", response_model=List[UnitResponse])
async def list_units(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar unidades"""
    return unit_controller(db).get_units(db, skip=skip, limit=limit)


@router.get("/{unit_id}", response_model=UnitResponse)
async def get_unit(unit_id: int, db: Session = Depends(get_db)):
    """Obter unidade por ID"""
    return unit_controller(db).get_unit_by_id(db, unit_id)


@router.put("/{unit_id}", response_model=UnitResponse)
async def update_unit(unit_id: int, unit_update: UnitUpdate, db: Session = Depends(get_db)):
    """Atualizar unidade"""
    return unit_controller(db).update_unit(db, unit_id, unit_update)


@router.delete("/{unit_id}")
async def delete_unit(unit_id: int, db: Session = Depends(get_db)):
    """Deletar unidade"""
    return unit_controller(db).delete_unit(db, unit_id)


@router.get("/property/{property_id}", response_model=List[UnitResponse])
async def get_units_by_property(property_id: int, db: Session = Depends(get_db)):
    """Obter unidades por propriedade"""
    return unit_controller(db).get_units_by_property(db, property_id)
