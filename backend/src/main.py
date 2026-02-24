import os

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.database import create_tables

# Importar routers de todos os módulos
from src.auth.router import router as auth_router
from src.properties.router import router as properties_router
from src.tenants.router import router as tenants_router
from src.contracts.router import router as contracts_router
from src.payments.router import router as payments_router
from src.expenses.router import router as expenses_router
from src.dashboard.router import router as dashboard_router
from src.notifications.router import router as notifications_router

# Inicializar aplicação FastAPI
app = FastAPI(
    title="Imobly - Gestão Imobiliária",
    description="API para gestão completa de propriedades imobiliárias com Supabase Auth",
    version="2.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

# Configuração CORS para comunicação com frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Middleware para capturar erros 500 e adicionar CORS headers
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        # Log do erro (em produção, use logging adequado)
        print(f"❌ Erro não tratado: {exc}")
        import traceback

        traceback.print_exc()

        # Retornar erro 500 com CORS habilitado
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Erro interno do servidor"},
            headers={
                "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
                "Access-Control-Allow-Credentials": "true",
            },
        )


# Criar diretório de uploads se não existir
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Servir arquivos estáticos (uploads) - apenas para fallback local
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Incluir routers com prefixos e tags
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(properties_router, prefix="/api/v1/properties", tags=["properties"])
app.include_router(tenants_router, prefix="/api/v1/tenants", tags=["tenants"])
app.include_router(contracts_router, prefix="/api/v1/contracts", tags=["contracts"])
app.include_router(payments_router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(expenses_router, prefix="/api/v1/expenses", tags=["expenses"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["notifications"])


@app.on_event("startup")
async def startup_event():
    """Executar na inicialização da aplicação"""
    # Criar tabelas no banco de dados
    create_tables()


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": f"Bem-vindo ao {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/api/v1/docs",
        "redoc": "/api/v1/redoc",
        "api": settings.API_V1_STR,
    }


@app.get("/health")
async def health_check():
    """Verificação de saúde da aplicação"""
    return {"status": "healthy", "service": settings.PROJECT_NAME}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)