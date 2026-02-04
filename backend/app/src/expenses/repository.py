from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository

from .models import Expense
from .schemas import ExpenseCreate, ExpenseUpdate


class ExpenseRepository(BaseRepository[Expense, ExpenseCreate, ExpenseUpdate]):
    """Repository para operações com despesas"""

    def __init__(self, db: Session):
        super().__init__(Expense)
        self.db = db

    def get_by_property(self, db: Session, property_id: int) -> List[Expense]:
        """Buscar despesas por propriedade"""
        return db.query(Expense).filter(Expense.property_id == property_id).all()

    def get_by_category(self, db: Session, category: str) -> List[Expense]:
        """Buscar despesas por categoria"""
        return db.query(Expense).filter(Expense.category == category).all()

    def get_by_status(self, db: Session, status: str) -> List[Expense]:
        """Buscar despesas por status"""
        return db.query(Expense).filter(Expense.status == status).all()

    def get_by_priority(self, db: Session, priority: str) -> List[Expense]:
        """Buscar despesas por prioridade"""
        return db.query(Expense).filter(Expense.priority == priority).all()

    def get_by_vendor(self, db: Session, vendor: str) -> List[Expense]:
        """Buscar despesas por fornecedor"""
        return db.query(Expense).filter(Expense.vendor == vendor).all()

    def get_urgent_expenses(self, db: Session) -> List[Expense]:
        """Buscar despesas urgentes (independente da categoria)"""
        return (
            db.query(Expense)
            .filter(
                Expense.priority == "urgent",
                Expense.status.in_(["pending", "scheduled"]),
            )
            .all()
        )

    def get_expenses_by_period(
        self, db: Session, start_date: date, end_date: date
    ) -> List[Expense]:
        """Buscar despesas por período"""
        return db.query(Expense).filter(Expense.date.between(start_date, end_date)).all()

    def get_pending_expenses(self, db: Session) -> List[Expense]:
        """Buscar despesas pendentes"""
        return self.get_by_status(db, "pending")

    def update_status(self, db: Session, expense_id: str, status: str) -> Optional[Expense]:
        """Atualizar status da despesa"""
        expense_obj = self.get(db, expense_id)
        if expense_obj:
            expense_obj.status = status
            db.commit()
            db.refresh(expense_obj)
            return expense_obj
        return None

    def get_categories(self, db: Session) -> List[str]:
        """Obter todas as categorias únicas"""
        result = db.query(Expense.category).distinct().all()
        return [row[0] for row in result]

    def get_vendors(self, db: Session) -> List[str]:
        """Obter todos os fornecedores únicos"""
        result = db.query(Expense.vendor).filter(Expense.vendor.isnot(None)).distinct().all()
        return [row[0] for row in result]


# Função para criar instância do repository
def get_expense_repository(db: Session) -> ExpenseRepository:
    return ExpenseRepository(db)
