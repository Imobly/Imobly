from fastapi import APIRouter

# NOTA: auth_router removido - autenticação gerenciada pelo Auth-api separado
from app.src.contracts.router import router as contracts_router
from app.src.dashboard.router import router as dashboard_router
from app.src.expenses.router import router as expenses_router
from app.src.notifications.router import router as notifications_router
from app.src.payments.router import router as payments_router

# Importar routers da nova estrutura src/
from app.src.properties.router import router as properties_router
from app.src.tenants.router import router as tenants_router
from app.src.units.router import router as units_router

api_router = APIRouter()

# NOTA: Router de autenticação removido - use Auth-api em localhost:5433

# Incluir todos os routers com seus prefixos e tags
api_router.include_router(properties_router, prefix="/properties", tags=["properties"])
api_router.include_router(tenants_router, prefix="/tenants", tags=["tenants"])
api_router.include_router(units_router, prefix="/units", tags=["units"])
api_router.include_router(contracts_router, prefix="/contracts", tags=["contracts"])
api_router.include_router(payments_router, prefix="/payments", tags=["payments"])
api_router.include_router(expenses_router, prefix="/expenses", tags=["expenses"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
