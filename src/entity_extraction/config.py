"""Configuration for entity extraction module."""

import logging
import os
from typing import Optional

from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


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
    cosmos_database: str = "underwriting"
    cosmos_container_schemas: str = "extraction_schemas"
    cosmos_container_models: str = "extraction_models"
    cosmos_container_results: str = "entities"  # Using entities container for extraction results
    
    # Azure OpenAI settings (optional - models from DB are preferred)
    openai_endpoint: Optional[str] = None
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
_cosmos_client: Optional[CosmosClient] = None
_credential: Optional[DefaultAzureCredential] = None
_initialized: bool = False


def get_config() -> ExtractionConfig:
    """Get or create global configuration instance."""
    global _config
    if _config is None:
        _config = ExtractionConfig()
        logger.info(f"[EXTRACTION CONFIG] Loaded config:")
        logger.info(f"  cosmos_endpoint: {_config.cosmos_endpoint}")
        logger.info(f"  cosmos_database: {_config.cosmos_database}")
        logger.info(f"  cosmos_key present: {bool(_config.cosmos_key)}")
        logger.info(f"  cosmos_key value (first 10 chars): {_config.cosmos_key[:10] if _config.cosmos_key else 'None'}...")
        
        # Debug: Check environment variables directly
        import os
        logger.info(f"  [ENV] EXTRACTION_COSMOS_KEY: {os.environ.get('EXTRACTION_COSMOS_KEY', 'NOT SET')[:10] if os.environ.get('EXTRACTION_COSMOS_KEY') else 'NOT SET'}...")
        logger.info(f"  [ENV] COSMOS_KEY: {os.environ.get('COSMOS_KEY', 'NOT SET')[:10] if os.environ.get('COSMOS_KEY') else 'NOT SET'}...")
    return _config


def get_cosmos_client() -> CosmosClient:
    """Get configured Cosmos DB client (cached singleton)."""
    global _cosmos_client, _credential, _initialized
    
    import threading
    current_thread = threading.current_thread().name
    
    logger.info(f"[EXTRACTION COSMOS] get_cosmos_client called from thread: {current_thread}")
    logger.info(f"[EXTRACTION COSMOS] _cosmos_client is None: {_cosmos_client is None}")
    logger.info(f"[EXTRACTION COSMOS] _initialized: {_initialized}")
    
    if _cosmos_client is not None:
        logger.info(f"[EXTRACTION COSMOS] Returning cached client")
        return _cosmos_client
    
    config = get_config()
    
    logger.info(f"[EXTRACTION COSMOS] Creating NEW Cosmos client...")
    logger.info(f"[EXTRACTION COSMOS] Endpoint: {config.cosmos_endpoint}")
    
    # FORCE AAD authentication - ignore any key that might be picked up
    # Cosmos DB has key auth disabled, so always use DefaultAzureCredential
    logger.info(f"[EXTRACTION COSMOS] Using DefaultAzureCredential (AAD auth) - FORCED")
    try:
        _credential = DefaultAzureCredential()
        logger.info(f"[EXTRACTION COSMOS] DefaultAzureCredential created")
        _cosmos_client = CosmosClient(config.cosmos_endpoint, credential=_credential)
        logger.info(f"[EXTRACTION COSMOS] CosmosClient created with AAD")
    except Exception as e:
        logger.error(f"[EXTRACTION COSMOS] FAILED to create client: {e}")
        raise
    
    _initialized = True
    logger.info(f"[EXTRACTION COSMOS] Client initialized successfully")
    return _cosmos_client
