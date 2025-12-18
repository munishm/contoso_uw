"""
Test fixtures and configuration for API tests.
"""

import pytest
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def mock_cosmos_client() -> MagicMock:
    """Create a mock Cosmos DB client."""
    client = MagicMock()
    client.get_database_client.return_value = MagicMock()
    return client


@pytest.fixture
def mock_blob_client() -> MagicMock:
    """Create a mock Blob Storage client."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_service_bus_client() -> MagicMock:
    """Create a mock Service Bus client."""
    client = MagicMock()
    return client


@pytest.fixture
def sample_case_data() -> dict:
    """Sample case data for testing."""
    return {
        "client_name": "John Smith",
        "policy_type": "Life Insurance - HNW",
        "submission_date": "2025-12-17",
        "metadata": {}
    }


@pytest.fixture
def sample_document_metadata() -> dict:
    """Sample document metadata for testing."""
    return {
        "document_id": "550e8400-e29b-41d4-a716-446655440000",
        "case_id": "CASE-202512-000001",
        "filename": "application_form.pdf",
        "content_type": "application/pdf",
        "size_bytes": 1048576,
        "processing_status": "pending"
    }


@pytest.fixture
def sample_entity_data() -> dict:
    """Sample entity data for testing."""
    return {
        "entity_id": "entity-550e8400-e29b-41d4-a716-446655440000",
        "entity_type": "person_name",
        "value": "John Smith",
        "normalized_value": "JOHN SMITH",
        "confidence": 0.92,
        "page_number": 1
    }


@pytest.fixture
def auth_headers() -> dict:
    """Mock authentication headers for testing."""
    return {
        "Authorization": "Bearer mock-jwt-token"
    }
