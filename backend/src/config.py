import os
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # JWT Settings
    # Fonte única do segredo de validação de JWT do Supabase.
    # Aceita SUPABASE_JWT_SECRET (preferido) ou SECRET_KEY (alias retrocompatível).
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET") or os.getenv("SECRET_KEY", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    # `SettingsConfigDict` substitui a `class Config`, removida no Pydantic v3.
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # Ignorar variáveis extras do Docker
    )

    @property
    def jwt_issuer(self) -> str | None:
        """
        Emissor esperado dos tokens: `{SUPABASE_URL}/auth/v1`.

        Validar o `iss` impede que um token legítimo de OUTRO projeto Supabase
        seja aceito aqui — o segredo é por projeto, mas a checagem torna a
        fronteira explícita e falha alto se a URL for trocada sem o segredo.
        """
        if not self.SUPABASE_URL:
            return None
        return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1"

    def validate_runtime(self) -> None:
        """
        Validações de inicialização (fail-fast). Chamada no startup da app.

        É preciso haver ALGUM jeito de validar assinatura de token:

        • Projetos novos do Supabase assinam com chave assimétrica (ES256) e
          publicam a pública no JWKS — basta `SUPABASE_URL`, não existe
          segredo compartilhado.
        • Projetos legados assinam com HS256 e exigem `SUPABASE_JWT_SECRET`.

        Exigir o segredo incondicionalmente quebrava projetos assimétricos, que
        legitimamente não têm um. Sem nenhum dos dois, porém, a aplicação não
        consegue autenticar ninguém e deve falhar no startup — não em produção,
        requisição a requisição.
        """
        if not self.SUPABASE_URL and not self.SUPABASE_JWT_SECRET:
            raise RuntimeError(
                "Nenhuma forma de validar tokens configurada: defina "
                "SUPABASE_URL (projetos com assinatura assimétrica, via JWKS) "
                "ou SUPABASE_JWT_SECRET (projetos legados, HS256)."
            )


settings = Settings()
