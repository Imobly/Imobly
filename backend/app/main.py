import os

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import create_tables

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

# Incluir rotas da API
app.include_router(api_router, prefix="/api/v1")


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
