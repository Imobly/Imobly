"""
Módulo src da aplicação Imobly
"""

# Importar todos os modelos para registrá-los com SQLAlchemy
from src.properties.models import Property
from src.tenants.models import Tenant  
from src.payments.models import Payment
from src.expenses.models import Expense

# Importar Base para garantir que esteja disponível
from src.database import Base

__all__ = ["Base", "Property", "Tenant", "Payment", "Expense"]