"""
FastAPI application entry point.

Configures the FastAPI application with middleware, routes, and lifespan events.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import __version__
from src.api.config.settings import get_settings
from src.api.middleware.correlation import CorrelationMiddleware
from src.api.middleware.error_handler import setup_exception_handlers
from src.api.middleware.logging import LoggingMiddleware
from src.api.repositories.base import cosmos_client
from src.api.routes import cases, documents, health, processing
from src.api.services.queue_service import queue_service
from src.api.services.storage_service import storage_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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

    try:
        # Initialize Cosmos DB client
        if settings.cosmos_endpoint:
            await cosmos_client.initialize(settings)
            logger.info("Cosmos DB client initialized")
        else:
            logger.warning("Cosmos DB not configured - some features may be unavailable")

        # Initialize Blob Storage
        if settings.blob_account_url or settings.blob_connection_string:
            await storage_service.initialize(settings)
            logger.info("Blob Storage client initialized")
        else:
            logger.warning("Blob Storage not configured - file upload disabled")

        # Initialize Service Bus
        if settings.service_bus_namespace or settings.service_bus_connection_string:
            await queue_service.initialize(settings)
            logger.info("Service Bus client initialized")
        else:
            logger.warning("Service Bus not configured - event publishing disabled")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        # Allow app to start even if some services fail
        # Health endpoint will report degraded status

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

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
