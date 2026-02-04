from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository

from .models import Payment
from .schemas import PaymentCreate, PaymentUpdate


class PaymentRepository(BaseRepository[Payment, PaymentCreate, PaymentUpdate]):
    """Repository para operações com pagamentos"""

    def __init__(self, db: Session):
        super().__init__(Payment)
        self.db = db

    def get_by_user(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Payment]:
        """Buscar pagamentos do usuário"""
        return db.query(Payment).filter(Payment.user_id == user_id).offset(skip).limit(limit).all()

    def get_by_id_and_user(self, db: Session, payment_id: int, user_id: int) -> Optional[Payment]:
        """Buscar pagamento por ID validando owner"""
        return (
            db.query(Payment).filter(Payment.id == payment_id, Payment.user_id == user_id).first()
        )

    def get_by_contract(self, db: Session, user_id: int, contract_id: int) -> List[Payment]:
        """Buscar pagamentos por contrato (filtrando por usuário)"""
        return (
            db.query(Payment)
            .filter(Payment.user_id == user_id, Payment.contract_id == contract_id)
            .all()
        )

    def get_by_tenant(self, db: Session, user_id: int, tenant_id: int) -> List[Payment]:
        """Buscar pagamentos por inquilino (filtrando por usuário)"""
        return (
            db.query(Payment)
            .filter(Payment.user_id == user_id, Payment.tenant_id == tenant_id)
            .all()
        )

    def get_by_property(self, db: Session, user_id: int, property_id: int) -> List[Payment]:
        """Buscar pagamentos por propriedade (filtrando por usuário)"""
        return (
            db.query(Payment)
            .filter(Payment.user_id == user_id, Payment.property_id == property_id)
            .all()
        )

    def get_by_status(self, db: Session, user_id: int, status: str) -> List[Payment]:
        """Buscar pagamentos por status (filtrando por usuário)"""
        return db.query(Payment).filter(Payment.user_id == user_id, Payment.status == status).all()

    def get_overdue_payments(self, db: Session, user_id: int) -> List[Payment]:
        """Buscar pagamentos em atraso (filtrando por usuário)"""
        return (
            db.query(Payment)
            .filter(
                Payment.user_id == user_id,
                Payment.status.in_(["pending", "partial"]),
                Payment.due_date < date.today(),
            )
            .all()
        )

    def get_pending_payments(self, db: Session, user_id: int) -> List[Payment]:
        """Buscar pagamentos pendentes (filtrando por usuário)"""
        return self.get_by_status(db, user_id, "pending")

    def get_payments_by_period(
        self,
        db: Session,
        user_id: int,
        start_date: date,
        end_date: date,
        payment_field: str = "due_date",
    ) -> List[Payment]:
        """Buscar pagamentos por período (filtrando por usuário)"""
        query = db.query(Payment).filter(Payment.user_id == user_id)
        if payment_field == "payment_date":
            return query.filter(Payment.payment_date.between(start_date, end_date)).all()
        else:
            return query.filter(Payment.due_date.between(start_date, end_date)).all()

    def update_payment_status(
        self,
        db: Session,
        payment_id: int,
        user_id: int,
        status: str,
        payment_date: Optional[date] = None,
        payment_method: Optional[str] = None,
    ) -> Optional[Payment]:
        """Atualizar status do pagamento (validando owner)"""
        payment_obj = self.get_by_id_and_user(db, payment_id, user_id)
        if payment_obj:
            payment_obj.status = status
            if payment_date:
                payment_obj.payment_date = payment_date
            if payment_method:
                payment_obj.payment_method = payment_method
            db.commit()
            db.refresh(payment_obj)
            return payment_obj
        return None

    def calculate_fine(self, db: Session, payment_id: int, user_id: int) -> Optional[Payment]:
        """Calcular multa automaticamente (validando owner)"""
        payment_obj = self.get_by_id_and_user(db, payment_id, user_id)
        if payment_obj and payment_obj.due_date < date.today():
            # Buscar taxa de multa do contrato
            from app.src.contracts.models import Contract

            contract = db.query(Contract).filter(Contract.id == payment_obj.contract_id).first()
            if contract:
                (date.today() - payment_obj.due_date).days
                fine_rate = float(contract.fine_rate) / 100
                payment_obj.fine_amount = payment_obj.amount * fine_rate
                payment_obj.total_amount = payment_obj.amount + payment_obj.fine_amount
                payment_obj.status = "overdue"
                db.commit()
                db.refresh(payment_obj)
                return payment_obj
        return None
