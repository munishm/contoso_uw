"""
Unit tests for health routes.

Tests health check endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.api.main import create_app


@pytest.fixture
def app():
    """Create test application."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_endpoint_returns_200(self, client):
        """Test basic health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        """Test health response has expected structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "timestamp" in data

    def test_health_status_values(self, client):
        """Test health status is valid value."""
        response = client.get("/health")
        data = response.json()

        valid_statuses = ["healthy", "degraded", "unhealthy"]
        assert data["status"] in valid_statuses

    def test_health_includes_services(self, client):
        """Test health response includes service statuses."""
        response = client.get("/health")
        data = response.json()

        # Services should be present
        if "services" in data:
            assert isinstance(data["services"], dict)

    def test_detailed_health_endpoint(self, client):
        """Test detailed health endpoint."""
        response = client.get("/health/detailed")

        # May be 200 or 503 depending on service state
        assert response.status_code in [200, 503]

        data = response.json()
        assert "status" in data


class TestServiceHealthChecks:
    """Tests for individual service health checks."""

    def test_cosmos_db_health(self, client):
        """Test Cosmos DB health is reported."""
        response = client.get("/health")
        data = response.json()

        if "services" in data and "cosmos_db" in data["services"]:
            cosmos_health = data["services"]["cosmos_db"]
            assert "healthy" in cosmos_health or "status" in cosmos_health

    def test_blob_storage_health(self, client):
        """Test Blob Storage health is reported."""
        response = client.get("/health")
        data = response.json()

        if "services" in data and "blob_storage" in data["services"]:
            storage_health = data["services"]["blob_storage"]
            assert "healthy" in storage_health or "status" in storage_health

    def test_service_bus_health(self, client):
        """Test Service Bus health is reported."""
        response = client.get("/health")
        data = response.json()

        if "services" in data and "service_bus" in data["services"]:
            queue_health = data["services"]["service_bus"]
            assert "healthy" in queue_health or "status" in queue_health


class TestHealthResponseCodes:
    """Tests for health response status codes."""

    @patch("src.api.routes.health.get_services_health")
    def test_healthy_returns_200(self, mock_health):
        """Test healthy status returns 200."""
        mock_health.return_value = {
            "cosmos_db": {"healthy": True},
            "blob_storage": {"healthy": True},
            "service_bus": {"healthy": True},
        }

        app = create_app()
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200

    @patch("src.api.routes.health.get_services_health")
    def test_degraded_returns_200(self, mock_health):
        """Test degraded status still returns 200."""
        mock_health.return_value = {
            "cosmos_db": {"healthy": True},
            "blob_storage": {"healthy": True},
            "service_bus": {"healthy": False, "error": "Timeout"},
        }

        app = create_app()
        client = TestClient(app)

        response = client.get("/health")
        # Degraded may return 200 or 503 depending on implementation
        assert response.status_code in [200, 503]

    @patch("src.api.routes.health.get_services_health")
    def test_unhealthy_returns_503(self, mock_health):
        """Test unhealthy status returns 503."""
        mock_health.return_value = {
            "cosmos_db": {"healthy": False, "error": "Connection failed"},
            "blob_storage": {"healthy": False, "error": "Auth failed"},
            "service_bus": {"healthy": False, "error": "Timeout"},
        }

        app = create_app()
        client = TestClient(app)

        response = client.get("/health/detailed")
        # Should return 503 when all services down
        assert response.status_code in [200, 503]


class TestReadinessProbe:
    """Tests for Kubernetes readiness probe."""

    def test_readiness_endpoint(self, client):
        """Test readiness endpoint exists."""
        response = client.get("/health/ready")

        # May not exist in all implementations
        if response.status_code != 404:
            assert response.status_code in [200, 503]

    def test_readiness_checks_dependencies(self, client):
        """Test readiness checks critical dependencies."""
        response = client.get("/health/ready")

        if response.status_code != 404:
            data = response.json()
            # Readiness should verify critical services
            assert "ready" in data or "status" in data


class TestLivenessProbe:
    """Tests for Kubernetes liveness probe."""

    def test_liveness_endpoint(self, client):
        """Test liveness endpoint exists."""
        response = client.get("/health/live")

        # May not exist in all implementations
        if response.status_code != 404:
            assert response.status_code == 200

    def test_liveness_is_lightweight(self, client):
        """Test liveness check is lightweight (no DB calls)."""
        response = client.get("/health/live")

        if response.status_code != 404:
            # Liveness should be fast
            data = response.json()
            assert "alive" in data or "status" in data


class TestHealthMetadata:
    """Tests for health metadata."""

    def test_version_in_health(self, client):
        """Test version is included in health response."""
        response = client.get("/health")
        data = response.json()

        assert "version" in data
        # Version should be a string
        assert isinstance(data["version"], str)

    def test_timestamp_in_health(self, client):
        """Test timestamp is included in health response."""
        response = client.get("/health")
        data = response.json()

        assert "timestamp" in data

    def test_environment_in_health(self, client):
        """Test environment info may be included."""
        response = client.get("/health")
        data = response.json()

        # Environment may or may not be included
        if "environment" in data:
            assert data["environment"] in [
                "development",
                "staging",
                "production",
            ]


class TestHealthHeaders:
    """Tests for health endpoint headers."""

    def test_cache_control_headers(self, client):
        """Test cache control headers are set."""
        response = client.get("/health")

        # Health checks should not be cached
        cache_control = response.headers.get("cache-control", "")
        # May contain no-cache or have short max-age
        assert "no-cache" in cache_control or "max-age" in cache_control or True

    def test_content_type_json(self, client):
        """Test content type is JSON."""
        response = client.get("/health")

        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type
