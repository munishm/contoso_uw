"""
Application settings using Pydantic BaseSettings.

Settings are loaded from environment variables with fallback to .env file.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="hsbc-iwpb-uw", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_version: str = Field(default="v1", alias="API_VERSION")

    # Azure Cosmos DB
    cosmos_endpoint: Optional[str] = Field(default=None, alias="COSMOS_ENDPOINT")
    cosmos_key: Optional[str] = Field(default=None, alias="COSMOS_KEY")
    cosmos_database_name: str = Field(default="underwriting", alias="COSMOS_DATABASE_NAME")

    # Azure Blob Storage
    blob_account_url: Optional[str] = Field(default=None, alias="BLOB_ACCOUNT_URL")
    blob_container_name: str = Field(default="documents", alias="BLOB_CONTAINER_NAME")
    blob_connection_string: Optional[str] = Field(default=None, alias="BLOB_CONNECTION_STRING")

    # Azure Service Bus
    service_bus_namespace: Optional[str] = Field(default=None, alias="SERVICE_BUS_NAMESPACE")
    service_bus_queue_name: str = Field(default="document-processing", alias="SERVICE_BUS_QUEUE_NAME")
    service_bus_connection_string: Optional[str] = Field(default=None, alias="SERVICE_BUS_CONNECTION_STRING")

    # Processing Configuration
    # When True, document processing happens synchronously in the API (no Service Bus)
    # When False, documents are queued to Service Bus for async processing
    sync_processing: bool = Field(default=True, alias="SYNC_PROCESSING")

    # API Configuration
    max_upload_size_mb: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")
    max_documents_per_case: int = Field(default=50, alias="MAX_DOCUMENTS_PER_CASE")
    sas_token_expiry_hours: int = Field(default=1, alias="SAS_TOKEN_EXPIRY_HOURS")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        alias="CORS_ORIGINS"
    )

    # Application Insights
    applicationinsights_connection_string: Optional[str] = Field(
        default=None, alias="APPLICATIONINSIGHTS_CONNECTION_STRING"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return upper_v

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
