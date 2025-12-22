"""
Unit tests for CaseService.

Tests business logic for case management operations.
"""

import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.services.case_service import CaseService
from src.api.models.case import CaseCreateRequest, CaseUpdateRequest
from src.api.models.enums import CaseStatus
from src.api.middleware.error_handler import NotFoundError, BadRequestError, ConflictError


@pytest.fixture
def mock_case_repo():
    """Create a mock case repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_document_repo():
    """Create a mock document repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_counter_repo():
    """Create a mock counter repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def case_service(mock_case_repo, mock_document_repo, mock_counter_repo):
    """Create a case service with mocked dependencies."""
    return CaseService(
        case_repository=mock_case_repo,
        document_repository=mock_document_repo,
        counter_repository=mock_counter_repo,
    )


@pytest.fixture
def sample_case():
    """Sample case document."""
    return {
        "id": "CASE-202512-000001",
        "case_id": "CASE-202512-000001",
        "client_name": "John Smith",
        "policy_type": "Life Insurance - HNW",
        "submission_date": "2025-12-17",
        "status": "draft",
        "created_at": "2025-12-17T10:00:00",
        "updated_at": "2025-12-17T10:00:00",
        "created_by": "user@example.com",
        "assigned_to": "underwriter@example.com",
        "metadata": {},
        "is_deleted": False,
        "deleted_at": None,
        "status_history": [
            {
                "previous_status": None,
                "new_status": "draft",
                "changed_by": "user@example.com",
                "changed_at": "2025-12-17T10:00:00",
                "reason": "Case created",
            }
        ],
    }


class TestCaseServiceCreate:
    """Tests for case creation."""

    @pytest.mark.asyncio
    async def test_create_case_success(self, case_service, mock_case_repo, mock_counter_repo, sample_case):
        """Test successful case creation."""
        # Arrange
        mock_counter_repo.get_next_case_id.return_value = "CASE-202512-000001"
        mock_case_repo.create_case.return_value = sample_case

        request = CaseCreateRequest(
            client_name="John Smith",
            policy_type="Life Insurance - HNW",
            submission_date=date(2025, 12, 17),
            assigned_to="underwriter@example.com",
        )

        # Act
        result = await case_service.create_case(request, "user@example.com")

        # Assert
        assert result.case_id == "CASE-202512-000001"
        assert result.client_name == "John Smith"
        assert result.status == CaseStatus.DRAFT
        mock_counter_repo.get_next_case_id.assert_called_once()
        mock_case_repo.create_case.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_case_generates_unique_id(self, case_service, mock_case_repo, mock_counter_repo, sample_case):
        """Test that case creation generates unique ID."""
        mock_counter_repo.get_next_case_id.return_value = "CASE-202512-000002"
        mock_case_repo.create_case.return_value = {**sample_case, "case_id": "CASE-202512-000002"}

        request = CaseCreateRequest(
            client_name="Jane Doe",
            policy_type="Life Insurance - HNW",
            submission_date=date(2025, 12, 17),
        )

        result = await case_service.create_case(request, "user@example.com")

        assert result.case_id == "CASE-202512-000002"


class TestCaseServiceGet:
    """Tests for retrieving cases."""

    @pytest.mark.asyncio
    async def test_get_case_success(self, case_service, mock_case_repo, mock_document_repo, sample_case):
        """Test successful case retrieval."""
        mock_case_repo.get_case.return_value = sample_case
        mock_document_repo.list_documents_for_case.return_value = []

        result = await case_service.get_case("CASE-202512-000001")

        assert result.case_id == "CASE-202512-000001"
        assert result.client_name == "John Smith"
        mock_case_repo.get_case.assert_called_once_with("CASE-202512-000001")

    @pytest.mark.asyncio
    async def test_get_case_not_found(self, case_service, mock_case_repo):
        """Test case not found raises NotFoundError."""
        mock_case_repo.get_case.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await case_service.get_case("CASE-NONEXISTENT")

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_deleted_case_raises_not_found(self, case_service, mock_case_repo, sample_case):
        """Test getting a deleted case raises NotFoundError."""
        deleted_case = {**sample_case, "is_deleted": True}
        mock_case_repo.get_case.return_value = deleted_case

        with pytest.raises(NotFoundError):
            await case_service.get_case("CASE-202512-000001")


class TestCaseServiceList:
    """Tests for listing cases."""

    @pytest.mark.asyncio
    async def test_list_cases_success(self, case_service, mock_case_repo, mock_document_repo, sample_case):
        """Test successful case listing."""
        mock_case_repo.list_cases.return_value = ([sample_case], 1)
        mock_document_repo.count_documents_for_case.return_value = 0

        result = await case_service.list_cases(page=1, page_size=20)

        assert len(result.items) == 1
        assert result.total == 1
        assert result.page == 1

    @pytest.mark.asyncio
    async def test_list_cases_with_status_filter(self, case_service, mock_case_repo, mock_document_repo, sample_case):
        """Test listing cases with status filter."""
        mock_case_repo.list_cases.return_value = ([sample_case], 1)
        mock_document_repo.count_documents_for_case.return_value = 0

        result = await case_service.list_cases(
            page=1,
            page_size=20,
            status=CaseStatus.DRAFT,
        )

        mock_case_repo.list_cases.assert_called_once()
        call_kwargs = mock_case_repo.list_cases.call_args[1]
        assert call_kwargs["filters"]["status"] == "draft"

    @pytest.mark.asyncio
    async def test_list_cases_pagination_validation(self, case_service):
        """Test pagination validation."""
        with pytest.raises(BadRequestError):
            await case_service.list_cases(page=0, page_size=20)

        with pytest.raises(BadRequestError):
            await case_service.list_cases(page=1, page_size=0)

        with pytest.raises(BadRequestError):
            await case_service.list_cases(page=1, page_size=101)

    @pytest.mark.asyncio
    async def test_list_cases_empty_result(self, case_service, mock_case_repo):
        """Test listing cases with empty result."""
        mock_case_repo.list_cases.return_value = ([], 0)

        result = await case_service.list_cases(page=1, page_size=20)

        assert len(result.items) == 0
        assert result.total == 0


class TestCaseServiceUpdate:
    """Tests for updating cases."""

    @pytest.mark.asyncio
    async def test_update_case_success(self, case_service, mock_case_repo, mock_document_repo, sample_case):
        """Test successful case update."""
        mock_case_repo.get_case.return_value = sample_case
        updated_case = {**sample_case, "client_name": "John Doe Updated"}
        mock_case_repo.update_case.return_value = updated_case
        mock_document_repo.list_documents_for_case.return_value = []

        request = CaseUpdateRequest(client_name="John Doe Updated")

        result = await case_service.update_case(
            "CASE-202512-000001",
            request,
            "user@example.com",
        )

        assert result.client_name == "John Doe Updated"

    @pytest.mark.asyncio
    async def test_update_case_not_found(self, case_service, mock_case_repo):
        """Test updating non-existent case raises NotFoundError."""
        mock_case_repo.get_case.return_value = None

        request = CaseUpdateRequest(client_name="Updated Name")

        with pytest.raises(NotFoundError):
            await case_service.update_case(
                "CASE-NONEXISTENT",
                request,
                "user@example.com",
            )


class TestCaseServiceDelete:
    """Tests for deleting cases."""

    @pytest.mark.asyncio
    async def test_soft_delete_case_success(self, case_service, mock_case_repo, sample_case):
        """Test successful soft delete."""
        mock_case_repo.get_case.return_value = sample_case
        deleted_case = {**sample_case, "is_deleted": True, "status": "deleted"}
        mock_case_repo.soft_delete_case.return_value = deleted_case

        await case_service.delete_case("CASE-202512-000001", "user@example.com")

        mock_case_repo.soft_delete_case.assert_called_once()

    @pytest.mark.asyncio
    async def test_soft_delete_case_not_found(self, case_service, mock_case_repo):
        """Test deleting non-existent case raises NotFoundError."""
        mock_case_repo.get_case.return_value = None

        with pytest.raises(NotFoundError):
            await case_service.delete_case("CASE-NONEXISTENT", "user@example.com")


class TestCaseServiceStatusTransition:
    """Tests for status transitions."""

    @pytest.mark.asyncio
    async def test_valid_status_transition(self, case_service, mock_case_repo, mock_document_repo, sample_case):
        """Test valid status transition from draft to in-review."""
        mock_case_repo.get_case.return_value = sample_case
        updated_case = {**sample_case, "status": "in-review"}
        mock_case_repo.update_case.return_value = updated_case
        mock_document_repo.list_documents_for_case.return_value = []

        request = CaseUpdateRequest(status=CaseStatus.IN_REVIEW)

        result = await case_service.update_case(
            "CASE-202512-000001",
            request,
            "user@example.com",
        )

        assert result.status == CaseStatus.IN_REVIEW
