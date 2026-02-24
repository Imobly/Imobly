"""
Repository para operações com pagamentos
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import Payment
from .schema import PaymentCreate, PaymentUpdate, PaymentCreateInternal


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
        db_payment = Payment(**payment_data.dict())
        self.db.add(db_payment)
        self.db.commit()
        self.db.refresh(db_payment)
        return db_payment

    def update(self, payment_id: int, user_id: int, update_data: PaymentUpdate) -> Optional[Payment]:
        """Atualizar pagamento"""
        db_payment = self.get_by_id_and_user(payment_id, user_id)
        if not db_payment:
            return None

        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(db_payment, field, value)

        self.db.commit()
        self.db.refresh(db_payment)
        return db_payment

    def delete(self, payment_id: int, user_id: int) -> bool:
        """Deletar pagamento"""
        db_payment = self.get_by_id_and_user(payment_id, user_id)
        if not db_payment:
            return False

        self.db.delete(db_payment)
        self.db.commit()
        return True

    def get_by_property(self, user_id: int, property_id: int) -> List[Payment]:
        """Buscar pagamentos por propriedade"""
        return (
            self.db.query(Payment)
            .filter(Payment.user_id == user_id, Payment.property_id == property_id)
            .all()
        )

    def get_by_tenant(self, user_id: int, tenant_id: int) -> List[Payment]:
        """Buscar pagamentos por inquilino"""
        return (
            self.db.query(Payment)
            .filter(Payment.user_id == user_id, Payment.tenant_id == tenant_id)
            .all()
        )

    def get_by_status(self, user_id: int, status: str) -> List[Payment]:
        """Buscar pagamentos por status"""
        return (
            self.db.query(Payment)
            .filter(Payment.user_id == user_id, Payment.status == status)
            .all()
        )

    def get_overdue_payments(self, user_id: int) -> List[Payment]:
        """Buscar pagamentos em atraso"""
        today = date.today()
        return (
            self.db.query(Payment)
            .filter(
                Payment.user_id == user_id,
                Payment.due_date < today,
                Payment.status.in_(["pending", "partial"])
            )
            .all()
        )
    
    def count_by_user(self, user_id: int) -> int:
        """Contar pagamentos do usuário"""
        return self.db.query(Payment).filter(Payment.user_id == user_id).count()
