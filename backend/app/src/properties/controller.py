from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .repository import PropertyRepository
from .schemas import PropertyCreate, PropertyResponse, PropertyUpdate


class property_controller:
    """Controller para gerenciar operações de propriedades"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = PropertyRepository(db)

    def get_properties(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        property_type: Optional[str] = None,
        status: Optional[str] = None,
        min_rent: Optional[float] = None,
        max_rent: Optional[float] = None,
        min_area: Optional[float] = None,
        max_area: Optional[float] = None,
    ) -> List[PropertyResponse]:
        """Listar propriedades com filtros opcionais"""

        # Se houver filtros, usar busca avançada
        if any([property_type, status, min_rent, max_rent, min_area, max_area]):
            return self.repository.search_properties(
                db=db,
                user_id=user_id,
                property_type=property_type,
                status=status,
                min_rent=min_rent,
                max_rent=max_rent,
                min_area=min_area,
                max_area=max_area,
                skip=skip,
                limit=limit,
            )

        # Caso contrário, usar listagem padrão
        return self.repository.get_by_user(db, user_id=user_id, skip=skip, limit=limit)

    def get_property_by_id(self, db: Session, property_id: int, user_id: int) -> PropertyResponse:
        """Obter propriedade por ID"""
        property_obj = self.repository.get_by_id_and_user(db, property_id, user_id)
        if not property_obj:
            raise HTTPException(status_code=404, detail="Imóvel não encontrado")
        return property_obj

    def create_property(
        self, db: Session, user_id: int, property_data: PropertyCreate
    ) -> PropertyResponse:
        """Criar nova propriedade"""
        # Adiciona user_id ao objeto Pydantic
        property_dict = property_data.model_dump()
        property_dict["user_id"] = user_id

        # Cria um novo objeto Pydantic com user_id incluído
        from app.src.properties.schemas import PropertyCreateInternal

        property_with_user = PropertyCreateInternal(**property_dict)

        return self.repository.create(db, obj_in=property_with_user)

    def update_property(
        self, db: Session, property_id: int, user_id: int, property_data: PropertyUpdate
    ) -> PropertyResponse:
        """Atualizar propriedade existente"""
        property_obj = self.repository.get_by_id_and_user(db, property_id, user_id)
        if not property_obj:
            raise HTTPException(status_code=404, detail="Imóvel não encontrado")

        return self.repository.update(db, db_obj=property_obj, obj_in=property_data)

    def delete_property(self, db: Session, property_id: int, user_id: int) -> dict:
        """Deletar propriedade"""
        property_obj = self.repository.get_by_id_and_user(db, property_id, user_id)
        if not property_obj:
            raise HTTPException(status_code=404, detail="Imóvel não encontrado")

        # Verificar se há contratos ativos vinculados à propriedade
        from app.src.contracts.models import Contract
        active_contracts = db.query(Contract).filter(
            Contract.property_id == property_id,
            Contract.status.in_(["active", "pending"])
        ).count()
        
        if active_contracts > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Não é possível deletar o imóvel. Existem {active_contracts} contrato(s) ativo(s) vinculado(s). Encerre os contratos antes de deletar o imóvel."
            )

        # Deletar imagens associadas
        if property_obj.images:
            from app.core.upload_service import upload_service
            upload_service.delete_multiple_files(property_obj.images)

        # Deletar a propriedade
        try:
            success = self.repository.delete(db, id=property_id)
            if not success:
                raise HTTPException(status_code=404, detail="Imóvel não encontrado")
            return {"message": "Imóvel deletado com sucesso"}
        except Exception as e:
            # Se houver erro de constraint (pagamentos, despesas, etc.), informar ao usuário
            error_msg = str(e)
            if "foreign key constraint" in error_msg.lower() or "violates" in error_msg.lower():
                raise HTTPException(
                    status_code=400,
                    detail="Não é possível deletar o imóvel. Existem registros vinculados (pagamentos, despesas, etc.). Remova-os antes de deletar o imóvel."
                )
            raise HTTPException(status_code=500, detail=f"Erro ao deletar imóvel: {error_msg}")

    def get_available_properties(self, db: Session, user_id: int) -> List[PropertyResponse]:
        """Obter apenas propriedades disponíveis"""
        return self.repository.get_available_properties(db, user_id)

    def update_property_status(
        self, db: Session, property_id: int, user_id: int, status: str
    ) -> PropertyResponse:
        """Atualizar apenas o status da propriedade"""
        valid_statuses = ["vacant", "occupied", "maintenance", "inactive"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, detail=f"Status inválido. Use: {', '.join(valid_statuses)}"
            )

        property_obj = self.repository.update_status(db, property_id, user_id, status)
        if not property_obj:
            raise HTTPException(status_code=404, detail="Imóvel não encontrado")
        return property_obj
