import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Imóvel Gestão API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    # Environment selector
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()

    # Database Settings
    # Unified env: prefer DATABASE_URL; else select by ENVIRONMENT
    DATABASE_URL_DEV: str = os.getenv(
        "DATABASE_URL_DEV", "postgresql://postgres:admin123@postgres:5432/imovel_gestao"
    )
    DATABASE_URL_HML: str | None = os.getenv("DATABASE_URL_HML")
    DATABASE_URL_PROD: str | None = os.getenv("DATABASE_URL_PROD")

    # Final DATABASE_URL resolution
    DATABASE_URL: str = os.getenv("DATABASE_URL") or (
        DATABASE_URL_DEV
        if ENVIRONMENT in {"dev", "development"}
        else (
            DATABASE_URL_HML
            if ENVIRONMENT in {"hml", "staging"}
            else (DATABASE_URL_PROD or DATABASE_URL_DEV)
        )
    )

    # Database Pool Settings
    # Configurações otimizadas para diferentes modos de conexão do PostgreSQL
    #
    # SUPABASE (Produção):
    #   - Transaction Mode (porta 6543): Recomendado! Suporta ~10.000 conexões
    #   - Session Mode (porta 5432): Limite baixo ~30 conexões
    #
    # LOCAL (Desenvolvimento):
    #   - Porta 5432: PostgreSQL local sem limites rigorosos
    #
    # Para alterar o modo no Supabase, mude a porta na DATABASE_URL:
    #   Session:     postgresql://...supabase.com:5432/postgres
    #   Transaction: postgresql://...supabase.com:6543/postgres
    #
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # 30min

    # Supabase Settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # Storage Settings
    STORAGE_MODE: str = os.getenv("STORAGE_MODE", "local")  # 'local' ou 'supabase'
    SUPABASE_PROPERTY_IMAGES_BUCKET: str = os.getenv("SUPABASE_PROPERTY_IMAGES_BUCKET", "property-images")
    SUPABASE_TENANT_DOCUMENTS_BUCKET: str = os.getenv("SUPABASE_TENANT_DOCUMENTS_BUCKET", "tenant-documents")
    SUPABASE_EXPENSE_DOCUMENTS_BUCKET: str = os.getenv("SUPABASE_EXPENSE_DOCUMENTS_BUCKET", "expense-documents")

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # CORS Settings - string env with comma-separated origins
    BACKEND_CORS_ORIGINS: str = os.getenv(
        "BACKEND_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    # File Upload Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx"}

    # Redis Settings (desabilitado - não sendo usado)
    # REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignorar variáveis extras do Docker


settings = Settings()
