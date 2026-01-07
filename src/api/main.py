"""
FastAPI application entry point.

Configures the FastAPI application with middleware, routes, and lifespan events.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config.settings import get_settings
from .middleware.correlation import CorrelationMiddleware
from .middleware.error_handler import setup_exception_handlers
from .middleware.logging import LoggingMiddleware
from .repositories.base import cosmos_client
from .routes import cases, documents, extraction, health, processing
from .services.queue_service import queue_service
from .services.storage_service import storage_service

# Configure logging
settings = get_settings()

# Use LOG_LEVEL from settings (defaults to INFO, can be set via env var)
log_level_name = settings.log_level.upper()
log_level = getattr(logging, log_level_name, logging.INFO)

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configure application module logging levels
# Set to WARNING to suppress debug/info logs, or use LOG_LEVEL for all
app_log_level = log_level if log_level_name == "DEBUG" else logging.INFO

# Suppress verbose logging from application modules (use LOG_LEVEL=DEBUG to enable)
logging.getLogger("src.orchestration").setLevel(app_log_level)
logging.getLogger("src.api.services").setLevel(app_log_level)
logging.getLogger("src.entity_extraction").setLevel(app_log_level)
logging.getLogger("src.document_classification").setLevel(app_log_level)
logging.getLogger("src.interfaces").setLevel(app_log_level)
logging.getLogger("src.api.repositories").setLevel(app_log_level)

# Reduce Azure SDK logging verbosity
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.core").setLevel(logging.WARNING)
logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("azure.cosmos").setLevel(logging.WARNING)
logging.getLogger("azure.storage").setLevel(logging.WARNING)
logging.getLogger("azure.servicebus").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    Initializes and cleans up resources on startup/shutdown.
    """
    settings = get_settings()

    # Startup
    logger.info(f"Starting {settings.app_name} v{__version__}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.debug}")

    # Initialize Cosmos DB client
    if settings.cosmos_endpoint:
        try:
            await cosmos_client.initialize(settings)
            logger.info("Cosmos DB client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}", exc_info=True)
    else:
        logger.warning("Cosmos DB not configured - COSMOS_ENDPOINT not set")

    # Pre-initialize extraction module's Cosmos client on main thread
    # This ensures DefaultAzureCredential works before ThreadPoolExecutor usage
    try:
        from src.entity_extraction.config import get_cosmos_client as get_extraction_cosmos_client
        _ = get_extraction_cosmos_client()
        logger.info("Extraction module Cosmos client pre-initialized")
    except Exception as e:
        logger.warning(f"Failed to pre-initialize extraction Cosmos client: {e}")

    # Initialize Blob Storage
    if settings.blob_account_url or settings.blob_connection_string:
        try:
            await storage_service.initialize(settings)
            logger.info("Blob Storage client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Blob Storage: {e}", exc_info=True)
    else:
        logger.warning("Blob Storage not configured - BLOB_ACCOUNT_URL not set")

    # Initialize Service Bus
    if settings.service_bus_namespace or settings.service_bus_connection_string:
        try:
            await queue_service.initialize(settings)
            logger.info("Service Bus client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Service Bus: {e}", exc_info=True)
    else:
        logger.warning("Service Bus not configured - SERVICE_BUS_NAMESPACE not set")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await cosmos_client.close()
    await storage_service.close()
    await queue_service.close()
    logger.info("Application shutdown complete")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Underwriting Case Management API",
        description=(
            "RESTful API for managing underwriting cases and documents. "
            "Enables underwriters to create cases, upload documents for automatic processing "
            "(classification, entity extraction, summarization), and retrieve analysis results."
        ),
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Add middleware (order matters - first added is outermost)
    # Correlation ID should be first to ensure all logs have correlation
    app.add_middleware(CorrelationMiddleware)

    # Logging middleware
    app.add_middleware(LoggingMiddleware)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],
    )

    # Setup exception handlers
    setup_exception_handlers(app)

    # Include routers
    api_prefix = f"/api/{settings.api_version}"

    # Health endpoint (no prefix, no auth)
    app.include_router(health.router)

    # API routes
    app.include_router(cases.router, prefix=api_prefix)
    app.include_router(documents.router, prefix=api_prefix)
    app.include_router(processing.router, prefix=api_prefix)
    app.include_router(extraction.router, prefix=api_prefix)

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
