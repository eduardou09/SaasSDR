from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Procura .env no diretório do backend e na raiz do monorepo
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # App
    # -------------------------------------------------------------------------
    app_name: str = "Convo"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    secret_key: str = "change-me"
    api_public_base_url: str = "http://localhost:8000"
    cors_origins: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://localhost:3001,"
        "http://127.0.0.1:3001,"
        "https://convo.app"
    )

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    database_url: str  # asyncpg
    sync_database_url: str = ""  # psycopg2 / sync (Alembic) — derivado de database_url se vazio

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_async_db_url(cls, v: str) -> str:
        """Normaliza para postgresql+asyncpg:// independente do formato recebido."""
        for prefix in ("postgresql+asyncpg://", "postgresql://", "postgres://"):
            if v.startswith(prefix):
                return "postgresql+asyncpg://" + v[len(prefix):]
        return v

    @model_validator(mode="after")
    def derive_sync_url(self) -> "Settings":
        """Se SYNC_DATABASE_URL não foi configurado, deriva de DATABASE_URL (remove +asyncpg)."""
        if not self.sync_database_url:
            self.sync_database_url = self.database_url.replace(
                "postgresql+asyncpg://", "postgresql://", 1
            )
        else:
            # Garante que não tem driver async no sync URL
            self.sync_database_url = self.sync_database_url.replace(
                "postgresql+asyncpg://", "postgresql://"
            ).replace("postgres://", "postgresql://")
        return self

    # -------------------------------------------------------------------------
    # Redis
    # -------------------------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"

    # -------------------------------------------------------------------------
    # Clerk
    # -------------------------------------------------------------------------
    clerk_secret_key: str
    clerk_publishable_key: str
    clerk_jwks_url: str  # ex: https://xxx.clerk.accounts.dev/.well-known/jwks.json
    clerk_webhook_secret: str = ""

    # -------------------------------------------------------------------------
    # Encryption (Fernet key para API keys dos clientes)
    # -------------------------------------------------------------------------
    encryption_key: str

    # -------------------------------------------------------------------------
    # Celery
    # -------------------------------------------------------------------------
    celery_broker_url: str = ""
    celery_result_backend: str = ""

    # -------------------------------------------------------------------------
    # Migrations
    # -------------------------------------------------------------------------
    run_migrations: bool = False

    # -------------------------------------------------------------------------
    # Observabilidade
    # -------------------------------------------------------------------------
    sentry_dsn: str = ""
    logfire_token: str = ""

    # -------------------------------------------------------------------------
    # LLMs do Convo (onboarder + supervisor — custo pago pelo Convo)
    # -------------------------------------------------------------------------
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # -------------------------------------------------------------------------
    # Z-API
    # -------------------------------------------------------------------------
    zapi_base_url: str = "https://api.z-api.io"

    # -------------------------------------------------------------------------
    # Stripe (Sprint 7)
    # -------------------------------------------------------------------------
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # -------------------------------------------------------------------------
    # Email (Sprint 7)
    # -------------------------------------------------------------------------
    resend_api_key: str = ""
    from_email: str = "no-reply@convo.app"

    # -------------------------------------------------------------------------
    # Computed properties
    # -------------------------------------------------------------------------
    @property
    def celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def celery_backend(self) -> str:
        return self.celery_result_backend or self.redis_url

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @field_validator("encryption_key")
    @classmethod
    def validate_fernet_key(cls, v: str) -> str:
        if v == "gere-com-o-comando-acima":
            return v  # Permite o placeholder no .env.example
        import base64

        try:
            decoded = base64.urlsafe_b64decode(v + "==")
            if len(decoded) != 32:
                raise ValueError("Fernet key deve ter 32 bytes")
        except Exception as e:
            raise ValueError(f"ENCRYPTION_KEY inválida: {e}") from e
        return v

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.environment == "production":
            if self.secret_key == "change-me-in-production-generate-with-openssl-rand-hex-32":
                raise ValueError("SECRET_KEY padrão não permitida em produção")
        return self


settings = Settings()
