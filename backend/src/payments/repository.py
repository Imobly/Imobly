"""
Repository para operações com pagamentos
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import Payment
from .schema import PaymentCreate, PaymentUpdate, PaymentCreateInternal

from src.core.tempo import hoje_brt


class PaymentRepository:
    """Repository para operações com pagamentos"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, payment_id: int) -> Optional[Payment]:
        """Buscar pagamento por ID"""
        return self.db.query(Payment).filter(Payment.id == payment_id).first()

    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Buscar pagamentos do usuário"""
        return (
            self.db.query(Payment)
            .filter(Payment.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id_and_user(self, payment_id: int, user_id: int) -> Optional[Payment]:
        """Buscar pagamento por ID e usuário"""
        return (
            self.db.query(Payment)
            .filter(Payment.id == payment_id, Payment.user_id == user_id)
            .first()
        )

    def create(self, payment_data: PaymentCreateInternal) -> Payment:
        """Criar um novo pagamento"""
        db_payment = Payment(**payment_data.model_dump())
        self.db.add(db_payment)
        self.db.commit()
        self.db.refresh(db_payment)
        return db_payment

    def update(
        self, payment_id: int, user_id: int, update_data: PaymentUpdate, commit: bool = True
    ) -> Optional[Payment]:
        """
        Atualizar pagamento.

        `commit=False` permite que a confirmação em lote seja uma transação só:
        antes era um commit por pagamento, e uma falha no meio deixava o lote
        parcialmente aplicado — respondendo 200 e omitindo o que falhou.
        """
        db_payment = self.get_by_id_and_user(payment_id, user_id)
        if not db_payment:
            return None

        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(db_payment, field, value)

        if commit:
            self.db.commit()
            self.db.refresh(db_payment)
        else:
            self.db.flush()
        return db_payment

    def delete(self, payment_id: int, user_id: int) -> bool:
        """Deletar pagamento"""
        db_payment = self.get_by_id_and_user(payment_id, user_id)
        if not db_payment:
            return False

        self.db.delete(db_payment)
        self.db.commit()
        return True

    def search(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        property_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        contract_id: Optional[int] = None,
    ) -> List[Payment]:
        """
        Busca com filtros COMBINÁVEIS e paginação sempre aplicada.

        Substitui os `get_by_*` que o router encadeava com if/elif: filtros
        além do primeiro eram descartados em silêncio (pedir
        `?property_id=1&status=atrasado` devolvia todos os pagamentos do
        imóvel, ignorando o status), e nenhum deles respeitava skip/limit —
        um usuário com muitos pagamentos recebia a tabela inteira.
        """
        query = self.db.query(Payment).filter(Payment.user_id == user_id)

        if status:
            query = query.filter(Payment.status == status)
        if property_id:
            query = query.filter(Payment.property_id == property_id)
        if tenant_id:
            query = query.filter(Payment.tenant_id == tenant_id)
        if contract_id:
            query = query.filter(Payment.contract_id == contract_id)

        return (
            query.order_by(Payment.due_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_property(self, user_id: int, property_id: int) -> List[Payment]:
        """Buscar pagamentos por propriedade"""
        return self.search(user_id, property_id=property_id, limit=1000)

    def get_by_tenant(self, user_id: int, tenant_id: int) -> List[Payment]:
        """Buscar pagamentos por inquilino"""
        return self.search(user_id, tenant_id=tenant_id, limit=1000)

    def get_by_status(self, user_id: int, status: str) -> List[Payment]:
        """Buscar pagamentos por status"""
        return self.search(user_id, status=status, limit=1000)

    def get_overdue_payments(self, user_id: int) -> List[Payment]:
        """Buscar pagamentos em atraso"""
        today = hoje_brt()
        return (
            self.db.query(Payment)
            .filter(
                Payment.user_id == user_id,
                Payment.due_date < today,
                Payment.status.in_(["pendente", "parcial"])
            )
            .all()
        )
    
    def count_by_user(self, user_id: int) -> int:
        """Contar pagamentos do usuário"""
        return self.db.query(Payment).filter(Payment.user_id == user_id).count()
