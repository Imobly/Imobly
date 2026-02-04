from datetime import date
from typing import Optional, Sequence

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.src.payments.repository import PaymentRepository

from .models import Contract
from .repository import ContractRepository
from .schemas import ContractCreate, ContractResponse, ContractUpdate


class contract_controller:
    """Controller para gerenciar operações de contratos"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ContractRepository(db)
        self.payment_repository = PaymentRepository(db)

    def get_contracts(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        property_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
    ) -> Sequence[Contract]:
        """Listar contratos com filtros"""
        if status:
            contracts = self.repository.get_by_status(db, status, user_id)
        elif property_id:
            contracts = self.repository.get_by_property(db, property_id, user_id)
        elif tenant_id:
            contracts = self.repository.get_by_tenant(db, tenant_id, user_id)
        else:
            contracts = self.repository.get_by_user(db, user_id, skip=skip, limit=limit)

        return contracts

    def get_contract_by_id(self, db: Session, contract_id: int, user_id: int) -> ContractResponse:
        """Obter contrato por ID"""
        contract_obj = self.repository.get_by_id_and_user(db, contract_id, user_id)
        if not contract_obj:
            raise HTTPException(status_code=404, detail="Contrato não encontrado")
        return contract_obj

    def create_contract(
        self, db: Session, user_id: int, contract_data: ContractCreate
    ) -> ContractResponse:
        """Criar novo contrato"""
        try:
            # Verificar se o título é único
            if not self.repository.check_unique_title(db, user_id, contract_data.title):
                raise HTTPException(
                    status_code=400,
                    detail="Já existe um contrato com este título"
                )
            
            # Verificar se propriedade está disponível no período
            if not self.repository.check_property_availability(
                db, contract_data.property_id, user_id, contract_data.start_date, contract_data.end_date
            ):
                raise HTTPException(
                    status_code=400, 
                    detail="Propriedade não disponível no período especificado. Já existe um contrato ativo que se sobrepõe a estas datas."
                )

            # Adiciona user_id ao objeto Pydantic
            contract_dict = contract_data.model_dump()
            contract_dict["user_id"] = user_id

            # Cria um novo objeto Pydantic com user_id incluído
            from app.src.contracts.schemas import ContractCreateInternal

            contract_with_user = ContractCreateInternal(**contract_dict)

            # Criar contrato
            new_contract = self.repository.create(db, obj_in=contract_with_user)
            
            # Se o contrato está ativo, atualizar status do imóvel para 'occupied'
            if contract_data.status == "active":
                from app.src.properties.models import Property
                property_obj = db.query(Property).filter(
                    Property.id == contract_data.property_id,
                    Property.user_id == user_id
                ).first()
                if property_obj:
                    property_obj.status = "occupied"
                    property_obj.tenant_id = contract_data.tenant_id
                    db.add(property_obj)
                    db.commit()
            
            return new_contract
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Erro ao criar contrato: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Erro ao criar contrato: {str(e)}")

    def update_contract(
        self, db: Session, contract_id: int, user_id: int, contract_data: ContractUpdate
    ) -> ContractResponse:
        """Atualizar contrato"""
        contract_obj = self.repository.get_by_id_and_user(db, contract_id, user_id)
        if not contract_obj:
            raise HTTPException(status_code=404, detail="Contrato não encontrado")

        # Se estiver atualizando o título, verificar se é único
        if contract_data.title and contract_data.title != contract_obj.title:
            if not self.repository.check_unique_title(db, user_id, contract_data.title, exclude_contract_id=contract_id):
                raise HTTPException(
                    status_code=400,
                    detail="Já existe um contrato com este título"
                )

        # Se estiver atualizando as datas, verificar disponibilidade
        if contract_data.start_date or contract_data.end_date:
            start = contract_data.start_date or contract_obj.start_date
            end = contract_data.end_date or contract_obj.end_date

            if not self.repository.check_property_availability(
                db, contract_obj.property_id, user_id, start, end, exclude_contract_id=contract_id
            ):
                raise HTTPException(
                    status_code=400, 
                    detail="Propriedade não disponível no período especificado. Já existe um contrato ativo que se sobrepõe a estas datas."
                )

        # Guardar status anterior
        old_status = contract_obj.status
        
        # Atualizar contrato
        updated_contract = self.repository.update(db, db_obj=contract_obj, obj_in=contract_data)
        
        # Atualizar status do imóvel se o status do contrato mudou
        if contract_data.status and contract_data.status != old_status:
            from app.src.properties.models import Property
            property_obj = db.query(Property).filter(
                Property.id == contract_obj.property_id,
                Property.user_id == user_id
            ).first()
            if property_obj:
                if contract_data.status == "active":
                    property_obj.status = "occupied"
                    property_obj.tenant_id = contract_obj.tenant_id
                elif contract_data.status in ["expired", "terminated"]:
                    property_obj.status = "vacant"
                    property_obj.tenant_id = None
                db.add(property_obj)
                db.commit()
        
        return updated_contract

    def delete_contract(self, db: Session, contract_id: int, user_id: int) -> dict:
        """Deletar contrato"""
        # Primeiro verifica se o contrato pertence ao usuário
        contract_obj = self.repository.get_by_id_and_user(db, contract_id, user_id)
        if not contract_obj:
            raise HTTPException(status_code=404, detail="Contrato não encontrado")

        success = self.repository.delete(db, id=contract_id)
        if not success:
            raise HTTPException(status_code=404, detail="Contrato não encontrado")
        return {"message": "Contrato deletado com sucesso"}

    def get_expiring_contracts(
        self, db: Session, user_id: int, days_ahead: int = 30
    ) -> Sequence[Contract]:
        """Obter contratos que vencem em breve"""
        return self.repository.get_expiring_contracts(db, user_id, days_ahead)

    def get_active_contracts(self, db: Session, user_id: int) -> Sequence[Contract]:
        """Obter contratos ativos"""
        return self.repository.get_active_contracts(db, user_id)

    def renew_contract(
        self,
        db: Session,
        contract_id: int,
        user_id: int,
        new_end_date: date,
        new_rent: Optional[float] = None,
    ) -> ContractResponse:
        """Renovar contrato"""
        contract_obj = self.repository.renew_contract(
            db, contract_id, user_id, new_end_date, new_rent
        )
        if not contract_obj:
            raise HTTPException(status_code=404, detail="Contrato não encontrado")
        return contract_obj


# Instância global do controller
