"""
Application configuration using Pydantic Settings.

This module provides environment-based configuration management for the
Email Token Authentication system. All settings are loaded from environment
variables with sensible defaults for development.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Uses Pydantic Settings for validation and type safety.
    Environment variables are automatically loaded from .env file.
    """

    # Application Settings
    app_name: str = Field(
        default="Email Token Auth", description="Application name displayed in API docs and emails"
    )

    app_env: str = Field(
        default="development",
        description="Application environment: development, staging, production, testing",
    )

    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT tokens and encryption. MUST be changed in production!",
    )

    # Token Settings
    token_expiry_minutes: int = Field(
        default=2, description="Token expiry time in minutes", ge=1, le=60
    )

    token_length: int = Field(
        default=6, description="Length of authentication token (number of digits)", ge=4, le=8
    )

    # Database Settings (Individual Components)
    postgres_user: str = Field(default="authuser", description="PostgreSQL username")

    postgres_password: str = Field(default="authpass123", description="PostgreSQL password")

    postgres_host: str = Field(default="database", description="PostgreSQL host address")

    postgres_port: str = Field(default="5432", description="PostgreSQL port")

    postgres_db: str = Field(default="auth_db", description="PostgreSQL database name")

    # Mailgun Settings
    mailgun_api_key: str = Field(default="", description="Mailgun API key for sending emails")

    mailgun_domain: str = Field(default="", description="Mailgun domain for sending emails")

    mailgun_from_email: str = Field(
        default="noreply@example.com", description="From email address for authentication emails"
    )

    mailgun_from_name: str = Field(
        default="Email Token Auth", description="From name for authentication emails"
    )

    # CORS Settings
    allowed_origins: str = Field(
        default="http://localhost:5173,http://localhost:5174",
        description="Comma-separated list of allowed CORS origins",
    )

    # Session Settings
    session_expiry_days: int = Field(
        default=7, description="Session expiry time in days", ge=1, le=30
    )

    # JWT Settings
    jwt_algorithm: str = Field(
        default="HS256", description="JWT signing algorithm (HS256, HS384, HS512)"
    )

    # Rate Limiting Settings
    rate_limit_requests: int = Field(
        default=3,
        description="Maximum token requests per email within rate limit window",
        ge=1,
        le=10,
    )

    rate_limit_window_minutes: int = Field(
        default=15, description="Rate limit window in minutes", ge=5, le=60
    )

    # Email Whitelist Settings
    enable_email_whitelist: bool = Field(
        default=True,
        description=(
            "Enable email whitelist - only emails in users table can "
            "request tokens. When True: only registered users can request "
            "tokens (secure, recommended). When False: any email can "
            "request a token (open registration mode). To bootstrap the "
            "first user, manually insert into database or disable "
            "temporarily."
        ),
    )

    # API Settings
    api_v1_prefix: str = Field(default="/api/v1", description="API version 1 prefix")

    # Branding Configuration (White-Label)
    company_name: str = Field(
        default="Email Token Auth",
        description="Company/brand name displayed in emails and communications",
    )

    support_email: str = Field(
        default="support@example.com", description="Support email address displayed in emails"
    )

    brand_primary_color: str = Field(
        default="#007bff", description="Primary brand color (hex format) for email templates"
    )

    email_template_path: str = Field(
        default="app/templates/email", description="Path to email template directory"
    )

    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """
        Construct async PostgreSQL connection URL from individual components.

        Returns:
            str: Async PostgreSQL connection URL for SQLAlchemy with asyncpg driver
        """
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allowed_origins_list(self) -> List[str]:
        """
        Parse allowed origins from comma-separated string to list.

        Returns:
            List[str]: List of allowed CORS origins
        """
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @field_validator("app_env")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """
        Validate that app_env is one of the allowed values.

        Args:
            v: The environment value to validate

        Returns:
            str: The validated environment value

        Raises:
            ValueError: If environment is not valid
        """
        allowed = ["development", "staging", "production", "testing"]
        if v.lower() not in allowed:
            raise ValueError(f"app_env must be one of {allowed}")
        return v.lower()

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """
        Validate that secret key is secure in production.

        Args:
            v: The secret key value
            info: Field validation info containing other field values

        Returns:
            str: The validated secret key

        Raises:
            ValueError: If secret key is insecure in production
        """
        # Get app_env from validation context
        app_env = info.data.get("app_env", "development")

        if app_env == "production" and v == "dev-secret-key-change-in-production":
            raise ValueError(
                "SECRET_KEY must be changed from default value in production! "
                "Generate a secure key using: openssl rand -hex 32"
            )

        if app_env == "production" and len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")

        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.app_env == "staging"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.app_env == "testing"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once and reused
    throughout the application lifecycle.

    Returns:
        Settings: Application settings instance

    Usage:
        from app.core.config import get_settings

        settings = get_settings()
        print(settings.app_name)
    """
    return Settings()


# Convenience export
settings = get_settings()
