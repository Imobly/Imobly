import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.config import settings
from src.core.rate_limit import limiter
from src.scheduler import start_scheduler, shutdown_scheduler

# Importar routers de todos os módulos
from src.auth.router import router as auth_router
from src.properties.router import router as properties_router
from src.tenants.router import router as tenants_router
from src.contracts.router import router as contracts_router
from src.payments.router import router as payments_router
from src.expenses.router import router as expenses_router
from src.dashboard.router import router as dashboard_router
from src.notifications.router import router as notifications_router

logger = logging.getLogger("imobly.main")

# Em produção, não expor a documentação interativa nem o schema OpenAPI
_IS_PROD = settings.ENVIRONMENT in {"prod", "production"}


# ── Lifespan (startup + shutdown) ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings.validate_runtime()
    # O schema é gerenciado exclusivamente pelo Alembic (`alembic upgrade head`),
    # executado como passo de deploy antes da aplicação subir. Criar tabelas aqui
    # mascarava a divergência entre os modelos e o banco real.
    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()


# Inicializar aplicação FastAPI
app = FastAPI(
    title="Imobly - Gestão Imobiliária",
    description="API para gestão completa de propriedades imobiliárias com Supabase Auth",
    version="2.0.0",
    openapi_url=None if _IS_PROD else "/api/v1/openapi.json",
    docs_url=None if _IS_PROD else "/api/v1/docs",
    redoc_url=None if _IS_PROD else "/api/v1/redoc",
    redirect_slashes=False,
    lifespan=lifespan,
)

# ── Rate limiting ──
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    429 com `Retry-After`, sem revelar quantas tentativas restam nem se a
    conta existe — a resposta é idêntica para usuário válido e inválido.
    """
    logger.warning(
        "Rate limit atingido em %s %s (origem %s)",
        request.method,
        request.url.path,
        request.client.host if request.client else "desconhecida",
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Muitas tentativas. Aguarde e tente novamente."},
        headers={"Retry-After": "60"},
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
    except Exception:
        logger.exception("Erro não tratado ao processar %s %s", request.method, request.url.path)

        # Só reflete a origem se ela estiver na allowlist — nunca ecoar
        # uma origem arbitrária junto de Allow-Credentials.
        origin = request.headers.get("origin")
        cors_headers = {}
        if origin and origin in settings.cors_origins_list:
            cors_headers = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
            }

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Erro interno do servidor"},
            headers=cors_headers,
        )


# Criar diretório de uploads se não existir (fallback local de escrita)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# ATENÇÃO — não remonte /uploads como StaticFiles.
# O mount servia todo o diretório sem autenticação: documentos de inquilinos
# (RG, CPF, CNH, comprovante de renda) ficavam acessíveis por URL adivinhável,
# já que o nome é `{timestamp}_{arquivo}`. Arquivos devem ser servidos apenas
# por endpoint autenticado que valide a posse e devolva uma signed URL de
# validade curta do Supabase Storage.

# Incluir routers com prefixos e tags
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(properties_router, prefix="/api/v1/properties", tags=["properties"])
app.include_router(tenants_router, prefix="/api/v1/tenants", tags=["tenants"])
app.include_router(contracts_router, prefix="/api/v1/contracts", tags=["contracts"])
app.include_router(payments_router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(expenses_router, prefix="/api/v1/expenses", tags=["expenses"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["notifications"])


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