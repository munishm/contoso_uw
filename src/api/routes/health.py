"""
Health check endpoint for service status monitoring.

Provides health status for the API and its dependent services.
"""

import logging

from fastapi import APIRouter, status

from src.api.models.common import HealthResponse
from src.api.repositories.base import cosmos_client
from src.api.services.queue_service import queue_service
from src.api.services.storage_service import storage_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check the health status of the API and its dependent services.",
)
async def health_check() -> HealthResponse:
    """
    Check health status of the API and dependent services.

    Returns status for:
    - Cosmos DB connection
    - Blob Storage connection
    - Service Bus connection
    """
    from src.api import __version__

    # Check Cosmos DB
    try:
        cosmos_status = "healthy" if cosmos_client._database else "not_initialized"
    except Exception as e:
        logger.warning(f"Cosmos DB health check failed: {e}")
        cosmos_status = "unhealthy"

    # Check Blob Storage
    try:
        blob_healthy = await storage_service.check_health()
        blob_status = "healthy" if blob_healthy else "unhealthy"
    except Exception as e:
        logger.warning(f"Blob Storage health check failed: {e}")
        blob_status = "not_initialized"

    # Check Service Bus
    try:
        queue_healthy = await queue_service.check_health()
        queue_status = "healthy" if queue_healthy else "unhealthy"
    except Exception as e:
        logger.warning(f"Service Bus health check failed: {e}")
        queue_status = "not_initialized"

    # Overall status
    all_healthy = all(
        s == "healthy" for s in [cosmos_status, blob_status, queue_status]
    )
    overall_status = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        status=overall_status,
        version=__version__,
        cosmos_db=cosmos_status,
        blob_storage=blob_status,
        service_bus=queue_status,
    )
