"""
Unit tests for CaseRepository.

Tests data access operations for cases.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime

from src.api.repositories.case_repository import CaseRepository
from src.api.models.enums import CaseStatus


@pytest.fixture
def mock_container():
    """Create a mock Cosmos DB container."""
    container = AsyncMock()
    container.create_item = AsyncMock()
    container.read_item = AsyncMock()
    container.replace_item = AsyncMock()
    container.delete_item = AsyncMock()
    container.query_items = MagicMock()
    return container


@pytest.fixture
def case_repository(mock_container):
    """Create a case repository with mocked container."""
    with patch.object(CaseRepository, 'container', new_callable=PropertyMock) as mock_prop:
        mock_prop.return_value = mock_container
        repo = CaseRepository()
        yield repo


@pytest.fixture
def sample_case_data():
    """Sample case data for testing."""
    return {
        "id": "CASE-202512-000001",
        "case_id": "CASE-202512-000001",
        "client_name": "John Smith",
        "policy_type": "Life Insurance - HNW",
        "submission_date": "2025-12-17",
        "status": "draft",
        "created_at": "2025-12-17T10:00:00Z",
        "updated_at": "2025-12-17T10:00:00Z",
        "created_by": "user@example.com",
        "assigned_to": "underwriter@example.com",
        "metadata": {},
        "is_deleted": False,
        "status_history": [],
    }


class TestCaseRepositoryCreate:
    """Tests for creating cases."""

    @pytest.mark.asyncio
    async def test_create_case_sets_defaults(self, case_repository, mock_container, sample_case_data):
        """Test that create_case sets default values."""
        mock_container.create_item.return_value = sample_case_data

        result = await case_repository.create_case({
            "case_id": "CASE-202512-000001",
            "client_name": "John Smith",
            "policy_type": "Life Insurance - HNW",
        })

        # Verify create_item was called
        mock_container.create_item.assert_called_once()
        call_args = mock_container.create_item.call_args[1]
        item = call_args["body"]

        # Check defaults are set
        assert "created_at" in item
        assert "updated_at" in item
        assert item.get("status") == CaseStatus.DRAFT.value
        assert item.get("deleted_at") is None

    @pytest.mark.asyncio
    async def test_create_case_adds_status_history(self, case_repository, mock_container, sample_case_data):
        """Test that create_case adds initial status history."""
        mock_container.create_item.return_value = sample_case_data

        await case_repository.create_case({
            "case_id": "CASE-202512-000001",
            "client_name": "John Smith",
            "created_by": "user@example.com",
        })

        call_args = mock_container.create_item.call_args[1]
        item = call_args["body"]

        assert "status_history" in item
        assert len(item["status_history"]) == 1
        assert item["status_history"][0]["new_status"] == CaseStatus.DRAFT.value


class TestCaseRepositoryGet:
    """Tests for retrieving cases."""

    @pytest.mark.asyncio
    async def test_get_case_by_id(self, case_repository, mock_container, sample_case_data):
        """Test getting a case by ID."""
        mock_container.read_item.return_value = sample_case_data

        result = await case_repository.get_case("CASE-202512-000001")

        assert result["case_id"] == "CASE-202512-000001"
        mock_container.read_item.assert_called_once_with(
            item="CASE-202512-000001",
            partition_key="CASE-202512-000001",
        )

    @pytest.mark.asyncio
    async def test_get_case_not_found_returns_none(self, case_repository, mock_container):
        """Test getting non-existent case returns None."""
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        mock_container.read_item.side_effect = CosmosResourceNotFoundError(
            status_code=404,
            message="Not found",
        )

        result = await case_repository.get_case("CASE-NONEXISTENT")

        assert result is None


class TestCaseRepositoryUpdate:
    """Tests for updating cases."""

    @pytest.mark.asyncio
    async def test_update_case_tracks_status_change(self, case_repository, mock_container, sample_case_data):
        """Test that update_case tracks status changes."""
        mock_container.read_item.return_value = sample_case_data
        updated_case = {**sample_case_data, "status": "in-review"}
        mock_container.replace_item.return_value = updated_case

        result = await case_repository.update_case(
            case_id="CASE-202512-000001",
            updates={"status": "in-review"},
            user_id="user@example.com",
        )

        mock_container.replace_item.assert_called_once()
        call_args = mock_container.replace_item.call_args[1]
        item = call_args["body"]

        # Check status history was updated
        assert len(item["status_history"]) > 0

    @pytest.mark.asyncio
    async def test_update_case_sets_updated_at(self, case_repository, mock_container, sample_case_data):
        """Test that update_case sets updated_at timestamp."""
        mock_container.read_item.return_value = sample_case_data
        mock_container.replace_item.return_value = sample_case_data

        await case_repository.update_case(
            case_id="CASE-202512-000001",
            updates={"client_name": "Jane Smith"},
            user_id="user@example.com",
        )

        call_args = mock_container.replace_item.call_args[1]
        item = call_args["body"]

        assert "updated_at" in item


class TestCaseRepositoryList:
    """Tests for listing cases."""

    @pytest.mark.asyncio
    async def test_list_cases_with_filters(self, case_repository, mock_container, sample_case_data):
        """Test listing cases with filters."""
        # Mock query results
        mock_query_result = MagicMock()
        mock_query_result.__aiter__ = lambda self: iter([sample_case_data])
        mock_container.query_items.return_value = mock_query_result

        # Mock count query
        async def mock_count(*args, **kwargs):
            return [{"count": 1}]

        with patch.object(case_repository, 'count', return_value=1):
            with patch.object(case_repository, 'query', return_value=[sample_case_data]):
                cases, total = await case_repository.list_cases(
                    filters={"status": "draft", "is_deleted": False},
                    limit=20,
                    offset=0,
                )

        assert total == 1
        assert len(cases) == 1

    @pytest.mark.asyncio
    async def test_list_cases_with_client_name_search(self, case_repository, mock_container, sample_case_data):
        """Test listing cases with client name search."""
        with patch.object(case_repository, 'count', return_value=1):
            with patch.object(case_repository, 'query', return_value=[sample_case_data]):
                cases, total = await case_repository.list_cases(
                    client_name_search="John",
                    limit=20,
                    offset=0,
                )

        assert total == 1


class TestCaseRepositorySoftDelete:
    """Tests for soft delete operations."""

    @pytest.mark.asyncio
    async def test_soft_delete_case(self, case_repository, mock_container, sample_case_data):
        """Test soft deleting a case."""
        mock_container.read_item.return_value = sample_case_data
        deleted_case = {**sample_case_data, "status": "deleted", "deleted_at": "2025-12-17T12:00:00Z"}
        mock_container.replace_item.return_value = deleted_case

        result = await case_repository.soft_delete_case(
            case_id="CASE-202512-000001",
            user_id="user@example.com",
        )

        assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_restore_case(self, case_repository, mock_container):
        """Test restoring a soft-deleted case."""
        deleted_case = {
            "case_id": "CASE-202512-000001",
            "status": "deleted",
            "previous_status": "draft",
            "deleted_at": "2025-12-17T12:00:00Z",
        }
        mock_container.read_item.return_value = deleted_case

        restored_case = {**deleted_case, "status": "draft", "deleted_at": None}
        mock_container.replace_item.return_value = restored_case

        result = await case_repository.restore_case(
            case_id="CASE-202512-000001",
            user_id="user@example.com",
        )

        assert result["status"] == "draft"
        assert result["deleted_at"] is None


class TestCaseRepositoryStatusHistory:
    """Tests for status history operations."""

    @pytest.mark.asyncio
    async def test_get_status_history(self, case_repository, mock_container):
        """Test getting status history."""
        case_with_history = {
            "case_id": "CASE-202512-000001",
            "status_history": [
                {"previous_status": None, "new_status": "draft"},
                {"previous_status": "draft", "new_status": "draft"},
            ],
        }
        mock_container.read_item.return_value = case_with_history

        history = await case_repository.get_status_history("CASE-202512-000001")

        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_get_status_history_case_not_found(self, case_repository, mock_container):
        """Test getting status history for non-existent case."""
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        mock_container.read_item.side_effect = CosmosResourceNotFoundError(
            status_code=404,
            message="Not found",
        )

        history = await case_repository.get_status_history("CASE-NONEXISTENT")

        assert history == []
