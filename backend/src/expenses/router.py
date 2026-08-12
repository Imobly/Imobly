"""
Router para o módulo de despesas
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.security import get_current_user_local_id
from src.core.ownership import assert_owned
from .repository import ExpenseRepository
from .schema import ExpenseCreate, ExpenseResponse, ExpenseUpdate, ExpenseCreateInternal

router = APIRouter()


def get_expense_repository(db: Session = Depends(get_db)) -> ExpenseRepository:
    """Dependency para obter repository de despesas"""
    return ExpenseRepository(db)


@router.get("/", response_model=List[ExpenseResponse])
def get_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    property_id: Optional[int] = Query(None, description="Filtrar por propriedade"),
    start_date: Optional[date] = Query(None, description="Data inicial"),
    end_date: Optional[date] = Query(None, description="Data final"),
    user_id: int = Depends(get_current_user_local_id),
    repository: ExpenseRepository = Depends(get_expense_repository),
):
    """Listar despesas com filtros opcionais"""

    if start_date and end_date:
        expenses = repository.get_by_date_range(user_id, start_date, end_date)
    elif property_id:
        expenses = repository.get_by_property(user_id, property_id)
    elif category:
        expenses = repository.get_by_category(user_id, category)
    elif status:
        expenses = repository.get_by_status(user_id, status)
    else:
        expenses = repository.get_by_user(user_id, skip, limit)
    
    return expenses


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense_data: ExpenseCreate,
    user_id: int = Depends(get_current_user_local_id),
    db: Session = Depends(get_db),
    repository: ExpenseRepository = Depends(get_expense_repository),
):
    """Criar nova despesa"""
    from src.properties.models import Property

    # property_id vem do cliente: valide a posse antes de gravar.
    assert_owned(db, Property, expense_data.property_id, user_id)

    expense_create_internal = ExpenseCreateInternal(
        **expense_data.dict(exclude={'user_id'}),
        user_id=user_id
    )
    
    new_expense = repository.create(expense_create_internal)
    return new_expense


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: str,
    user_id: int = Depends(get_current_user_local_id),
    repository: ExpenseRepository = Depends(get_expense_repository),
):
    """Obter despesa por ID"""

    expense = repository.get_by_id_and_user(expense_id, user_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Despesa não encontrada"
        )
    return expense


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: str,
    expense_data: ExpenseUpdate,
    user_id: int = Depends(get_current_user_local_id),
    repository: ExpenseRepository = Depends(get_expense_repository),
):
    """Atualizar despesa"""

    updated_expense = repository.update(expense_id, user_id, expense_data)
    if not updated_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Despesa não encontrada"
        )
    return updated_expense


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: str,
    user_id: int = Depends(get_current_user_local_id),
    repository: ExpenseRepository = Depends(get_expense_repository),
):
    """Deletar despesa"""

    success = repository.delete(expense_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Despesa não encontrada"
        )
    return {"message": "Despesa deletada com sucesso"}


@router.get("/statistics/monthly")
def get_monthly_expenses(
    year: int = Query(..., description="Ano"),
    month: int = Query(..., ge=1, le=12, description="Mês"),
    user_id: int = Depends(get_current_user_local_id),
    repository: ExpenseRepository = Depends(get_expense_repository),
):
    """Obter total de despesas do mês"""
    total = repository.get_monthly_total(user_id, year, month)
    return {"year": year, "month": month, "total": total}

