"""
Guardian Configuration - Pydantic Settings

Environment-based configuration for the Guardian authentication service.
All settings are loaded from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses Pydantic Settings for validation and type safety.
    """

    # Application Settings
    app_name: str = Field(
        default="Guardian",
        description="Application name"
    )

    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )

    environment: str = Field(
        default="development",
        description="Application environment: development, staging, production"
    )

    debug: bool = Field(
        default=True,
        description="Enable debug mode"
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    secret_key: str = Field(
        default="guardian-dev-secret-key-change-in-production",
        description="Secret key for JWT tokens. MUST be changed in production!"
    )

    # API Settings
    api_prefix: str = Field(
        default="/api",
        description="API prefix path"
    )

    # Token Settings
    token_expiry_minutes: int = Field(
        default=10,
        ge=1,
        le=60,
        description="6-digit token expiry time in minutes"
    )

    token_length: int = Field(
        default=6,
        ge=4,
        le=8,
        description="Length of authentication token (number of digits)"
    )

    # Session Settings
    session_expiry_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="JWT session expiry time in days"
    )

    # JWT Settings
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )

    # Database Settings
    postgres_user: str = Field(
        default="guardian",
        description="PostgreSQL username"
    )

    postgres_password: str = Field(
        default="guardian123",
        description="PostgreSQL password"
    )

    postgres_host: str = Field(
        default="database",
        description="PostgreSQL host"
    )

    postgres_port: str = Field(
        default="5432",
        description="PostgreSQL port"
    )

    postgres_db: str = Field(
        default="guardian_db",
        description="PostgreSQL database name"
    )

    # Email Settings (Mailgun)
    mailgun_api_key: str = Field(
        default="",
        description="Mailgun API key"
    )

    mailgun_domain: str = Field(
        default="",
        description="Mailgun domain"
    )

    mailgun_from_email: str = Field(
        default="noreply@guardian.local",
        description="From email address"
    )

    mailgun_from_name: str = Field(
        default="Guardian Auth",
        description="From name"
    )

    # CORS Settings
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated list of allowed CORS origins"
    )

    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS"
    )

    cors_methods: str = Field(
        default="GET,POST,PUT,PATCH,DELETE,OPTIONS",
        description="Allowed HTTP methods"
    )

    cors_headers: str = Field(
        default="*",
        description="Allowed headers"
    )

    # Rate Limiting
    rate_limit_requests: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum token requests per email within rate limit window"
    )

    rate_limit_window_minutes: int = Field(
        default=15,
        ge=5,
        le=60,
        description="Rate limit window in minutes"
    )

    # Email Whitelist
    enable_email_whitelist: bool = Field(
        default=False,
        description="Only allow registered emails to request tokens"
    )

    # Bolt Gateway Settings
    bolt_gateway_enabled: bool = Field(
        default=False,
        description="Enable Bolt gateway validation"
    )

    bolt_gateway_header: str = Field(
        default="X-Forwarded-By",
        description="Header name for gateway validation"
    )

    bolt_gateway_value: str = Field(
        default="bolt-gateway",
        description="Expected header value from gateway"
    )

    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @computed_field
    @property
    def database_url(self) -> str:
        """Construct async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @computed_field
    @property
    def cors_methods_list(self) -> List[str]:
        """Parse CORS methods from comma-separated string."""
        return [m.strip() for m in self.cors_methods.split(",") if m.strip()]

    @computed_field
    @property
    def cors_headers_list(self) -> List[str]:
        """Parse CORS headers from comma-separated string."""
        if self.cors_headers == "*":
            return ["*"]
        return [h.strip() for h in self.cors_headers.split(",") if h.strip()]

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v.lower() not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v.lower()

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Validate secret key is secure in production."""
        env = info.data.get("environment", "development")
        if env == "production":
            if "dev" in v.lower() or "change" in v.lower():
                raise ValueError("SECRET_KEY must be changed in production!")
            if len(v) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
