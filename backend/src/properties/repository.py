"""
Repository para operações com propriedades
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from .models import Property
from .schema import PropertyCreate, PropertyUpdate, PropertyCreateInternal


class PropertyRepository:
    """Repository para operações com propriedades"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, property_id: int) -> Optional[Property]:
        """Buscar propriedade por ID"""
        return self.db.query(Property).filter(Property.id == property_id).first()

    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Property]:
        """Buscar propriedades do usuário"""
        return (
            self.db.query(Property)
            .filter(Property.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id_and_user(self, property_id: int, user_id: int) -> Optional[Property]:
        """Buscar propriedade por ID e usuário"""
        return (
            self.db.query(Property)
            .filter(Property.id == property_id, Property.user_id == user_id)
            .first()
        )

    def create(self, property_data: PropertyCreateInternal) -> Property:
        """Criar uma nova propriedade"""
        db_property = Property(**property_data.dict())
        self.db.add(db_property)
        self.db.commit()
        self.db.refresh(db_property)
        return db_property

    def update(self, property_id: int, user_id: int, update_data: PropertyUpdate) -> Optional[Property]:
        """Atualizar propriedade"""
        db_property = self.get_by_id_and_user(property_id, user_id)
        if not db_property:
            return None

        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(db_property, field, value)

        self.db.commit()
        self.db.refresh(db_property)
        return db_property

    def delete(self, property_id: int, user_id: int) -> bool:
        """Deletar propriedade"""
        db_property = self.get_by_id_and_user(property_id, user_id)
        if not db_property:
            return False

        self.db.delete(db_property)
        self.db.commit()
        return True

    def get_by_status(self, user_id: int, status: str) -> List[Property]:
        """Buscar propriedades por status (filtrando por usuário)"""
        return (
            self.db.query(Property)
            .filter(Property.user_id == user_id, Property.status == status)
            .all()
        )

    def get_by_property_type(self, user_id: int, property_type: str) -> List[Property]:
        """Buscar propriedades por tipo (filtrando por usuário)"""
        return (
            self.db.query(Property)
            .filter(Property.user_id == user_id, Property.type == property_type)
            .all()
        )

    def search_properties(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        property_type: Optional[str] = None,
        status: Optional[str] = None,
        min_rent: Optional[float] = None,
        max_rent: Optional[float] = None,
        min_area: Optional[float] = None,
        max_area: Optional[float] = None,
        neighborhood: Optional[str] = None,
        city: Optional[str] = None
    ) -> List[Property]:
        """Buscar propriedades com filtros"""
        query = self.db.query(Property).filter(Property.user_id == user_id)

        if property_type:
            query = query.filter(Property.type == property_type)
        if status:
            query = query.filter(Property.status == status)
        if min_rent is not None:
            query = query.filter(Property.rent >= min_rent)
        if max_rent is not None:
            query = query.filter(Property.rent <= max_rent)
        if min_area is not None:
            query = query.filter(Property.area >= min_area)
        if max_area is not None:
            query = query.filter(Property.area <= max_area)
        if neighborhood:
            query = query.filter(Property.neighborhood.ilike(f"%{neighborhood}%"))
        if city:
            query = query.filter(Property.city.ilike(f"%{city}%"))

        return query.offset(skip).limit(limit).all()

    def count_by_user(self, user_id: int) -> int:
        """Contar propriedades do usuário"""
        return self.db.query(Property).filter(Property.user_id == user_id).count()

    def get_vacant_properties(self, user_id: int) -> List[Property]:
        """Obter propriedades vagas"""
        return self.get_by_status(user_id, "vacant")

    def get_occupied_properties(self, user_id: int) -> List[Property]:
        """Obter propriedades ocupadas"""
        return self.get_by_status(user_id, "occupied")

    def count_by_status(self, user_id: int) -> Dict[str, int]:
        """Contar propriedades por status em uma única consulta SQL (GROUP BY)"""
        rows = (
            self.db.query(Property.status, func.count(Property.id))
            .filter(Property.user_id == user_id)
            .group_by(Property.status)
            .all()
        )
        return {status: count for status, count in rows}