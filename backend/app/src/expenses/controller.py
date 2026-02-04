from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .repository import ExpenseRepository
from .schemas import ExpenseCreate, ExpenseResponse, ExpenseUpdate


class expense_controller:
    """Controller para gerenciar operações de despesas"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ExpenseRepository(db)

    def get_expenses(self, db: Session, skip: int = 0, limit: int = 100) -> List[ExpenseResponse]:
        """Listar despesas"""
        return self.repository.get_multi(db, skip=skip, limit=limit)

    def get_expenses_by_property(self, db: Session, property_id: int) -> List[ExpenseResponse]:
        """Obter despesas por propriedade"""
        return self.repository.get_by_property(db, property_id=property_id)

    def get_expense_by_id(self, db: Session, expense_id: int) -> ExpenseResponse:
        """Obter despesa por ID"""
        expense_obj = self.repository.get(db, expense_id)
        if not expense_obj:
            raise HTTPException(status_code=404, detail="Despesa não encontrada")
        return expense_obj

    def create_expense(self, db: Session, expense_data: ExpenseCreate) -> ExpenseResponse:
        """Criar nova despesa"""
        return self.repository.create(db, obj_in=expense_data)

    def update_expense(
        self, db: Session, expense_id: int, expense_data: ExpenseUpdate
    ) -> ExpenseResponse:
        """Atualizar despesa existente"""
        expense_obj = self.repository.get(db, expense_id)
        if not expense_obj:
            raise HTTPException(status_code=404, detail="Despesa não encontrada")

        return self.repository.update(db, db_obj=expense_obj, obj_in=expense_data)

    def delete_expense(self, db: Session, expense_id: int) -> dict:
        """Deletar despesa"""
        success = self.repository.delete(db, id=expense_id)
        if not success:
            raise HTTPException(status_code=404, detail="Despesa não encontrada")
        return {"message": "Despesa deletada com sucesso"}


# Instância global do controller
