from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository

from .models import Property
from .schemas import PropertyCreate, PropertyUpdate


class PropertyRepository(BaseRepository[Property, PropertyCreate, PropertyUpdate]):
    """Repository para operações com propriedades"""

    def __init__(self, db: Session):
        super().__init__(Property)
        self.db = db

    def get_by_user(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Property]:
        """Buscar propriedades do usuário"""
        return (
            db.query(Property).filter(Property.user_id == user_id).offset(skip).limit(limit).all()
        )

    def get_by_id_and_user(self, db: Session, property_id: int, user_id: int) -> Optional[Property]:
        """Buscar propriedade por ID e usuário"""
        return (
            db.query(Property)
            .filter(Property.id == property_id, Property.user_id == user_id)
            .first()
        )

    def get_by_status(self, db: Session, user_id: int, status: str) -> List[Property]:
        """Buscar propriedades por status (filtrando por usuário)"""
        return (
            db.query(Property).filter(Property.user_id == user_id, Property.status == status).all()
        )

    def get_by_property_type(self, db: Session, user_id: int, property_type: str) -> List[Property]:
        """Buscar propriedades por tipo (filtrando por usuário)"""
        return (
            db.query(Property)
            .filter(Property.user_id == user_id, Property.type == property_type)
            .all()
        )

    def search_properties(
        self,
        db: Session,
        user_id: int,
        *,
        property_type: Optional[str] = None,
        status: Optional[str] = None,
        min_rent: Optional[float] = None,
        max_rent: Optional[float] = None,
        min_area: Optional[float] = None,
        max_area: Optional[float] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Property]:
        """Buscar propriedades com filtros avançados (filtrando por usuário)"""
        query = db.query(Property).filter(Property.user_id == user_id)

        if property_type:
            query = query.filter(Property.type == property_type)

        if status:
            query = query.filter(Property.status == status)

        if min_rent:
            query = query.filter(Property.rent >= min_rent)

        if max_rent:
            query = query.filter(Property.rent <= max_rent)

        if min_area:
            query = query.filter(Property.area >= min_area)

        if max_area:
            query = query.filter(Property.area <= max_area)

        return query.offset(skip).limit(limit).all()

    def get_available_properties(self, db: Session, user_id: int) -> List[Property]:
        """Buscar apenas propriedades disponíveis (filtrando por usuário)"""
        return self.get_by_status(db, user_id, "vacant")

    def update_status(
        self, db: Session, property_id: int, user_id: int, status: str
    ) -> Optional[Property]:
        """Atualizar apenas o status da propriedade (validando owner)"""
        property_obj = self.get_by_id_and_user(db, property_id, user_id)
        if property_obj:
            property_obj.status = status
            db.commit()
            db.refresh(property_obj)
            return property_obj
        return None
