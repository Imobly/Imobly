"""
Repository para operações com despesas
"""

import uuid
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract

from .models import Expense
from .schema import ExpenseCreate, ExpenseUpdate, ExpenseCreateInternal


class ExpenseRepository:
    """Repository para operações com despesas"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, expense_id: str) -> Optional[Expense]:
        """Buscar despesa por ID"""
        return self.db.query(Expense).filter(Expense.id == expense_id).first()

    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Expense]:
        """Buscar despesas do usuário"""
        return (
            self.db.query(Expense)
            .filter(Expense.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id_and_user(self, expense_id: str, user_id: int) -> Optional[Expense]:
        """Buscar despesa por ID e usuário"""
        return (
            self.db.query(Expense)
            .filter(Expense.id == expense_id, Expense.user_id == user_id)
            .first()
        )

    def create(self, expense_data: ExpenseCreateInternal) -> Expense:
        """Criar uma nova despesa"""
        expense_dict = expense_data.dict()
        expense_dict['id'] = str(uuid.uuid4())
        db_expense = Expense(**expense_dict)
        self.db.add(db_expense)
        self.db.commit()
        self.db.refresh(db_expense)
        return db_expense

    def update(self, expense_id: str, user_id: int, update_data: ExpenseUpdate) -> Optional[Expense]:
        """Atualizar despesa"""
        db_expense = self.get_by_id_and_user(expense_id, user_id)
        if not db_expense:
            return None

        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(db_expense, field, value)

        self.db.commit()
        self.db.refresh(db_expense)
        return db_expense

    def delete(self, expense_id: str, user_id: int) -> bool:
        """Deletar despesa"""
        db_expense = self.get_by_id_and_user(expense_id, user_id)
        if not db_expense:
            return False

        self.db.delete(db_expense)
        self.db.commit()
        return True

    def get_by_property(self, user_id: int, property_id: int) -> List[Expense]:
        """Buscar despesas por propriedade"""
        return (
            self.db.query(Expense)
            .filter(Expense.user_id == user_id, Expense.property_id == property_id)
            .all()
        )

    def get_by_category(self, user_id: int, category: str) -> List[Expense]:
        """Buscar despesas por categoria"""
        return (
            self.db.query(Expense)
            .filter(Expense.user_id == user_id, Expense.category == category)
            .all()
        )

    def get_by_status(self, user_id: int, status: str) -> List[Expense]:
        """Buscar despesas por status"""
        return (
            self.db.query(Expense)
            .filter(Expense.user_id == user_id, Expense.status == status)
            .all()
        )

    def get_by_date_range(self, user_id: int, start_date: date, end_date: date) -> List[Expense]:
        """Buscar despesas por período"""
        return (
            self.db.query(Expense)
            .filter(
                Expense.user_id == user_id,
                Expense.date >= start_date,
                Expense.date <= end_date
            )
            .all()
        )

    def get_monthly_total(self, user_id: int, year: int, month: int) -> float:
        """Obter total de despesas do mês"""
        result = (
            self.db.query(func.sum(Expense.amount))
            .filter(
                Expense.user_id == user_id,
                extract('year', Expense.date) == year,
                extract('month', Expense.date) == month
            )
            .scalar()
        )
        return float(result) if result else 0.0
    
    def count_by_user(self, user_id: int) -> int:
        """Contar despesas do usuário"""
        return self.db.query(Expense).filter(Expense.user_id == user_id).count()
