"""Configuration for entity extraction module."""

import os
from typing import Optional

from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExtractionConfig(BaseSettings):
    """Configuration settings for schema-based extraction."""
    
    model_config = SettingsConfigDict(
        env_prefix="EXTRACTION_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Cosmos DB settings
    cosmos_endpoint: str
    cosmos_key: Optional[str] = None
    cosmos_database: str = "extraction_db"
    cosmos_container_schemas: str = "extraction_schemas"
    cosmos_container_models: str = "extraction_models"
    cosmos_container_results: str = "extraction_results"
    
    # Azure OpenAI settings
    openai_endpoint: str
    openai_key: Optional[str] = None
    openai_api_version: str = "2024-02-15-preview"
    openai_deployment_gpt4_vision: str = "gpt-4-vision"
    
    # Azure Document Intelligence settings (optional, added in Phase 4)
    doc_intelligence_endpoint: Optional[str] = None
    doc_intelligence_key: Optional[str] = None
    
    # Cache settings
    schema_cache_ttl_seconds: int = 300  # 5 minutes
    
    # Performance settings
    max_concurrent_extractions: int = 10
    extraction_timeout_seconds: int = 120  # 2 minutes


# Global configuration instance
_config: Optional[ExtractionConfig] = None


def get_config() -> ExtractionConfig:
    """Get or create global configuration instance."""
    global _config
    if _config is None:
        _config = ExtractionConfig()
    return _config


def get_cosmos_client() -> CosmosClient:
    """Get configured Cosmos DB client."""
    config = get_config()
    
    if config.cosmos_key:
        # Use key-based authentication
        return CosmosClient(config.cosmos_endpoint, credential=config.cosmos_key)
    else:
        # Use managed identity / DefaultAzureCredential
        credential = DefaultAzureCredential()
        return CosmosClient(config.cosmos_endpoint, credential=credential)
