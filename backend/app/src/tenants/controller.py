from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .repository import TenantRepository
from .schemas import TenantCreate, TenantResponse, TenantUpdate


class tenant_controller:
    """Controller para gerenciar operações de inquilinos"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = TenantRepository(db)

    def get_tenants(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        name: Optional[str] = None,
        email: Optional[str] = None,
        cpf: Optional[str] = None,
    ) -> List[TenantResponse]:
        """Listar inquilinos com filtros opcionais"""

        # Se houver filtros, usar busca avançada
        if any([name, email, cpf]):
            return self.repository.search_tenants(
                db=db, user_id=user_id, name=name, email=email, cpf=cpf, skip=skip, limit=limit
            )

        # Caso contrário, usar listagem padrão
        return self.repository.get_by_user(db, user_id, skip=skip, limit=limit)

    def get_tenant_by_id(self, db: Session, tenant_id: int, user_id: int) -> TenantResponse:
        """Obter inquilino por ID"""
        tenant_obj = self.repository.get_by_id_and_user(db, tenant_id, user_id)
        if not tenant_obj:
            raise HTTPException(status_code=404, detail="Inquilino não encontrado")
        return tenant_obj

    def get_tenant_by_email(self, db: Session, email: str, user_id: int) -> TenantResponse:
        """Obter inquilino por email"""
        tenant_obj = self.repository.get_by_email(db, user_id, email)
        if not tenant_obj:
            raise HTTPException(status_code=404, detail="Inquilino não encontrado")
        return tenant_obj

    def get_tenant_by_cpf(self, db: Session, cpf: str, user_id: int) -> TenantResponse:
        """Obter inquilino por CPF"""
        tenant_obj = self.repository.get_by_cpf(db, user_id, cpf)
        if not tenant_obj:
            raise HTTPException(status_code=404, detail="Inquilino não encontrado")
        return tenant_obj

    def create_tenant(self, db: Session, user_id: int, tenant_data: TenantCreate) -> TenantResponse:
        """Criar novo inquilino"""

        # Verificar se email e CPF são únicos
        validation_errors = self.repository.check_unique_constraints(db, user_id, tenant_data)
        if validation_errors:
            # Formatar mensagem de erro mais amigável
            error_messages = ", ".join([f"{k}: {v}" for k, v in validation_errors.items()])
            raise HTTPException(status_code=400, detail=f"Dados duplicados: {error_messages}")

        # Adiciona user_id ao objeto Pydantic
        tenant_dict = tenant_data.model_dump()
        tenant_dict["user_id"] = user_id

        # Cria um novo objeto Pydantic com user_id incluído
        from app.src.tenants.schemas import TenantCreateInternal

        tenant_with_user = TenantCreateInternal(**tenant_dict)

        return self.repository.create(db, obj_in=tenant_with_user)

    def update_tenant(
        self, db: Session, tenant_id: int, user_id: int, tenant_data: TenantUpdate
    ) -> TenantResponse:
        """Atualizar inquilino existente"""
        tenant_obj = self.repository.get_by_id_and_user(db, tenant_id, user_id)
        if not tenant_obj:
            raise HTTPException(status_code=404, detail="Inquilino não encontrado")

        # Verificar se email e CPF são únicos (excluindo o próprio registro)
        if hasattr(tenant_data, "email") and tenant_data.email:
            tenant_create_data = TenantCreate(**tenant_data.dict())
            validation_errors = self.repository.check_unique_constraints(
                db, user_id, tenant_create_data, exclude_id=tenant_id
            )
            if validation_errors:
                raise HTTPException(status_code=400, detail=validation_errors)

        return self.repository.update(db, db_obj=tenant_obj, obj_in=tenant_data)

    def delete_tenant(self, db: Session, tenant_id: int, user_id: int) -> dict:
        """Deletar inquilino"""
        tenant_obj = self.repository.get_by_id_and_user(db, tenant_id, user_id)
        if not tenant_obj:
            raise HTTPException(status_code=404, detail="Inquilino não encontrado")

        # Verificar se há contratos ativos vinculados ao inquilino
        from app.src.contracts.models import Contract
        active_contracts = db.query(Contract).filter(
            Contract.tenant_id == tenant_id,
            Contract.status.in_(["active", "pending"])
        ).count()
        
        if active_contracts > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Não é possível deletar o inquilino. Existem {active_contracts} contrato(s) ativo(s) vinculado(s). Encerre os contratos antes de deletar o inquilino."
            )

        # Deletar documentos associados
        if tenant_obj.documents:
            from app.core.upload_service import upload_service
            upload_service.delete_multiple_files(tenant_obj.documents)

        # Deletar o inquilino
        try:
            success = self.repository.delete(db, id=tenant_id)
            if not success:
                raise HTTPException(status_code=404, detail="Inquilino não encontrado")
            return {"message": "Inquilino deletado com sucesso"}
        except Exception as e:
            error_msg = str(e)
            if "foreign key constraint" in error_msg.lower() or "violates" in error_msg.lower():
                raise HTTPException(
                    status_code=400,
                    detail="Não é possível deletar o inquilino. Existem registros vinculados (pagamentos, contratos, etc.). Remova-os antes de deletar o inquilino."
                )
            raise HTTPException(status_code=500, detail=f"Erro ao deletar inquilino: {error_msg}")

    def validate_tenant_exists(self, db: Session, tenant_id: int, user_id: int) -> bool:
        """Validar se inquilino existe (útil para outras operações)"""
        return self.repository.get_by_id_and_user(db, tenant_id, user_id) is not None


# Instância global do controller
