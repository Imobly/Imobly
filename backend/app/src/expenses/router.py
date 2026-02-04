from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_id_from_token
from app.core.upload_service import upload_service
from app.db.session import get_db

from .repository import get_expense_repository
from .schemas import ExpenseCreate, ExpenseResponse, ExpenseUpdate

router = APIRouter()


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense: ExpenseCreate,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Criar nova despesa"""
    # Criar despesa com user_id do token
    expense_data = expense.model_dump()
    expense_data["user_id"] = user_id

    # Criar modelo Expense
    from .models import Expense

    db_expense = Expense(**expense_data)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.get("/", response_model=List[ExpenseResponse])
async def list_expenses(
    skip: int = 0,
    limit: int = 100,
    property_id: int = None,
    category: str = None,
    month: int = None,
    year: int = None,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Listar despesas do usuário autenticado"""

    # Buscar apenas despesas do usuário autenticado (multi-tenancy)
    from .models import Expense

    query = db.query(Expense).filter(Expense.user_id == user_id)

    # Aplicar filtros
    if property_id:
        query = query.filter(Expense.property_id == property_id)
    if category:
        query = query.filter(Expense.category == category)

    # Filtrar por mês/ano se especificado
    if year:
        from sqlalchemy import extract

        query = query.filter(extract("year", Expense.date) == year)
    if month:
        from sqlalchemy import extract

        query = query.filter(extract("month", Expense.date) == month)

    expenses = query.offset(skip).limit(limit).all()
    return expenses


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: str,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Obter despesa por ID (apenas do usuário autenticado)"""
    expense_repo = get_expense_repository(db)
    expense = expense_repo.get(db, expense_id)

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada")

    # Verificar se a despesa pertence ao usuário (multi-tenancy)
    if expense.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    return expense


@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: str,
    expense_update: ExpenseUpdate,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Atualizar despesa (apenas do usuário autenticado)"""
    expense_repo = get_expense_repository(db)
    expense = expense_repo.get(db, expense_id)

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada")

    # Verificar se a despesa pertence ao usuário (multi-tenancy)
    if expense.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    updated_expense = expense_repo.update(db, db_obj=expense, obj_in=expense_update)
    return updated_expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: str,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Deletar despesa (apenas do usuário autenticado)"""
    expense_repo = get_expense_repository(db)
    expense = expense_repo.get(db, expense_id)

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada")

    # Verificar se a despesa pertence ao usuário (multi-tenancy)
    if expense.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    expense_repo.delete(db, id=expense_id)


@router.get("/property/{property_id}/monthly", response_model=dict)
async def get_monthly_expenses(
    property_id: int, year: int, month: int, db: Session = Depends(get_db)
):
    """Obter despesas mensais de uma propriedade"""
    expense_repo = get_expense_repository(db)
    expenses = expense_repo.get_by_property(db, property_id)

    # Filtrar por mês/ano
    monthly_expenses = []
    for expense in expenses:
        if expense.date.year == year and expense.date.month == month:
            monthly_expenses.append(expense)

    total = sum(expense.amount for expense in monthly_expenses)

    return {
        "property_id": property_id,
        "year": year,
        "month": month,
        "total_expenses": total,
        "count": len(monthly_expenses),
        "expenses": monthly_expenses,
    }


@router.get("/categories/summary", response_model=dict)
async def get_expenses_by_category(
    property_id: int = None, year: int = None, month: int = None, db: Session = Depends(get_db)
):
    """Obter resumo de despesas por categoria"""
    expense_repo = get_expense_repository(db)
    expenses = expense_repo.get_multi(db)

    # Aplicar filtros
    if property_id:
        expenses = [e for e in expenses if e.property_id == property_id]
    if year:
        expenses = [e for e in expenses if e.date.year == year]
    if month:
        expenses = [e for e in expenses if e.date.month == month]

    # Agrupar por categoria
    categories = {}
    for expense in expenses:
        if expense.category not in categories:
            categories[expense.category] = {"total": 0, "count": 0, "expenses": []}
        categories[expense.category]["total"] += expense.amount
        categories[expense.category]["count"] += 1
        categories[expense.category]["expenses"].append(expense)

    return {"categories": categories}


# ==================== UPLOAD ENDPOINTS ====================


@router.post("/{expense_id}/upload-documents", status_code=status.HTTP_201_CREATED)
async def upload_expense_documents(
    expense_id: str,
    files: List[UploadFile] = File(..., description="Documentos/comprovantes (imagens ou PDFs)"),
    document_type: str = Query(
        "comprovante", description="Tipo: comprovante, nota_fiscal, recibo, outros"
    ),
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    Upload de múltiplos documentos/comprovantes para uma despesa

    - Aceita até 5 arquivos por requisição
    - Formatos: JPG, JPEG, PNG, PDF
    - Tamanho máximo: 10MB por arquivo
    - Documentos são adicionados ao array existente
    """
    from datetime import datetime

    # Validar número de arquivos
    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Número máximo de arquivos excedido. Máximo: 5",
        )

    # Verificar se a despesa existe
    expense_repo = get_expense_repository(db)
    expense = expense_repo.get(db, expense_id)

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada")

    # Verificar permissão (multi-tenancy)
    if expense.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    # Upload dos arquivos
    uploaded_files = []
    for file in files:
        file_info = await upload_service.save_file(
            file=file, folder=f"expenses/{expense_id}", allowed_types="all"
        )

        # Criar objeto de documento
        document = {
            "id": file_info["filename"].split(".")[0],
            "name": file_info["original_filename"],
            "type": document_type,
            "url": file_info["url"],
            "file_type": file_info["type"],
            "size": file_info["size"],
            "uploaded_at": datetime.now().isoformat(),
        }

        uploaded_files.append(file_info)

        # Adicionar ao array de documentos
        if expense.documents is None:
            expense.documents = []
        expense.documents.append(document)

    # Atualizar no banco
    db.commit()
    db.refresh(expense)

    return {
        "message": f"{len(files)} documento(s) enviado(s) com sucesso",
        "uploaded_files": uploaded_files,
        "total_documents": len(expense.documents) if expense.documents else 0,
    }


@router.get("/{expense_id}/documents")
async def list_expense_documents(
    expense_id: str,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    Listar todos os documentos de uma despesa
    """
    expense_repo = get_expense_repository(db)
    expense = expense_repo.get(db, expense_id)

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada")

    # Verificar permissão
    if expense.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    return {
        "expense_id": expense_id,
        "documents": expense.documents or [],
        "total_documents": len(expense.documents) if expense.documents else 0,
    }


@router.delete("/{expense_id}/documents")
async def delete_expense_document(
    expense_id: str,
    document_url: str = Query(..., description="URL do documento a ser deletado"),
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    Deletar um documento específico de uma despesa

    - Remove o arquivo do servidor
    - Remove do array de documentos no banco
    """
    expense_repo = get_expense_repository(db)
    expense = expense_repo.get(db, expense_id)

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada")

    # Verificar permissão
    if expense.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    # Verificar se existe documentos
    if not expense.documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum documento encontrado para esta despesa",
        )

    # Procurar e remover documento
    document_found = False
    updated_documents = []
    file_to_delete = None

    for doc in expense.documents:
        if doc.get("url") == document_url:
            document_found = True
            file_to_delete = document_url
        else:
            updated_documents.append(doc)

    if not document_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado"
        )

    # Deletar arquivo físico do Supabase
    try:
        if file_to_delete:
            upload_service.delete_file(file_to_delete)
    except Exception as e:
        print(f"⚠️ Erro ao deletar arquivo do Supabase: {e}")
        # Continua mesmo se falhar a deleção do arquivo

    # Atualizar array no banco
    expense.documents = updated_documents
    db.commit()
    db.refresh(expense)

    return {
        "message": "Documento deletado com sucesso",
        "file_deleted": True,
        "remaining_documents": len(expense.documents),
    }


# ==================== ENDPOINTS LEGADOS (COMPATIBILIDADE) ====================


@router.post("/{expense_id}/upload-receipt", status_code=status.HTTP_201_CREATED)
async def upload_expense_receipt(
    expense_id: str,
    file: UploadFile = File(..., description="Nota fiscal ou comprovante (imagem ou PDF)"),
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    Upload de nota fiscal ou comprovante de despesa

    - Aceita imagens (JPG, PNG) ou PDF
    - Tamanho máximo: 10MB
    - Substitui o arquivo anterior se já existir
    """
    # Verificar se a despesa existe
    expense_repo = get_expense_repository(db)
    expense = expense_repo.get(db, expense_id)

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada")

    # Verificar se a despesa pertence ao usuário (quando multi-tenancy for implementado)
    # if expense.user_id != user_id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    # Se já existe um recibo, deletar o arquivo antigo
    if expense.receipt:
        upload_service.delete_file(expense.receipt)

    # Salvar novo arquivo
    file_info = await upload_service.save_file(
        file=file, folder=f"expenses/{expense_id}", allowed_types="all"  # Permite imagens e PDFs
    )

    # Atualizar despesa com URL do novo recibo
    expense_repo.update(db, db_obj=expense, obj_in=ExpenseUpdate(receipt=file_info["url"]))

    return {
        "message": "Comprovante enviado com sucesso",
        "file_info": file_info,
        "expense_id": expense_id,
    }


@router.delete("/{expense_id}/receipt")
async def delete_expense_receipt(
    expense_id: str,
    user_id: int = Depends(get_current_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    Deletar comprovante de uma despesa

    - Remove o arquivo do servidor
    - Limpa o campo receipt no banco de dados
    """
    # Verificar se a despesa existe
    expense_repo = get_expense_repository(db)
    expense = expense_repo.get(db, expense_id)

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada")

    # Verificar se existe um recibo
    if not expense.receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum comprovante encontrado para esta despesa",
        )

    # Deletar arquivo físico
    deleted = upload_service.delete_file(expense.receipt)

    # Limpar campo no banco
    expense_repo.update(db, db_obj=expense, obj_in=ExpenseUpdate(receipt=None))

    return {"message": "Comprovante deletado com sucesso", "file_deleted": deleted}
