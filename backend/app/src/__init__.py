"""
Source module - Todos os módulos de domínio da aplicação
"""

# Importar todos os módulos para facilitar acesso
from . import contracts, dashboard, expenses, notifications, payments, properties, tenants, units

__all__ = [
    "properties",
    "tenants",
    "contracts",
    "payments",
    "expenses",
    "notifications",
    "units",
    "dashboard",
]
