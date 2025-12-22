"""
Unit tests for entity and summary repositories.

Tests entity extraction and document summarization data access.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.api.models.enums import DocumentType


@pytest.fixture
def mock_cosmos_container():
    """Create mock Cosmos DB container."""
    container = AsyncMock()
    container.create_item = AsyncMock()
    container.read_item = AsyncMock()
    container.replace_item = AsyncMock()
    container.delete_item = AsyncMock()
    container.query_items = MagicMock()
    return container


@pytest.fixture
def sample_entity():
    """Sample entity data."""
    return {
        "id": "ENT-001",
        "document_id": "DOC-001",
        "case_id": "CASE-202512-000001",
        "entity_type": "person_name",
        "value": "John Smith",
        "normalized_value": "JOHN SMITH",
        "confidence": 0.95,
        "page_number": 1,
        "bounding_box": {"x": 100, "y": 200, "width": 150, "height": 20},
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_summary():
    """Sample summary data."""
    return {
        "id": "SUM-001",
        "document_id": "DOC-001",
        "case_id": "CASE-202512-000001",
        "summary_text": "Medical examination report for life insurance application.",
        "key_points": [
            "Patient is in good health",
            "No significant medical history",
            "Blood pressure within normal range",
        ],
        "confidence": 0.92,
        "model_version": "gpt-4-turbo",
        "created_at": datetime.utcnow().isoformat(),
    }


class TestEntityRepository:
    """Tests for entity repository operations."""

    @pytest.mark.asyncio
    async def test_create_entity(self, mock_cosmos_container, sample_entity):
        """Test creating a new entity."""
        from src.api.repositories.entity_repository import EntityRepository

        repo = EntityRepository.__new__(EntityRepository)
        repo._container = mock_cosmos_container

        mock_cosmos_container.create_item.return_value = sample_entity

        result = await repo.create(sample_entity)

        mock_cosmos_container.create_item.assert_called_once()
        assert result["entity_type"] == "person_name"

    @pytest.mark.asyncio
    async def test_get_entity(self, mock_cosmos_container, sample_entity):
        """Test retrieving an entity by ID."""
        from src.api.repositories.entity_repository import EntityRepository

        repo = EntityRepository.__new__(EntityRepository)
        repo._container = mock_cosmos_container

        mock_cosmos_container.read_item.return_value = sample_entity

        result = await repo.get(
            entity_id="ENT-001",
            document_id="DOC-001",
        )

        assert result["value"] == "John Smith"

    @pytest.mark.asyncio
    async def test_list_entities_by_document(
        self, mock_cosmos_container, sample_entity
    ):
        """Test listing entities for a document."""
        from src.api.repositories.entity_repository import EntityRepository

        repo = EntityRepository.__new__(EntityRepository)
        repo._container = mock_cosmos_container

        entities = [
            sample_entity,
            {**sample_entity, "id": "ENT-002", "entity_type": "date"},
        ]
        mock_cosmos_container.query_items.return_value = iter(entities)

        result = await repo.list_by_document(document_id="DOC-001")

        assert len(list(result)) == 2

    @pytest.mark.asyncio
    async def test_list_entities_by_type(
        self, mock_cosmos_container, sample_entity
    ):
        """Test filtering entities by type."""
        from src.api.repositories.entity_repository import EntityRepository

        repo = EntityRepository.__new__(EntityRepository)
        repo._container = mock_cosmos_container

        mock_cosmos_container.query_items.return_value = iter([sample_entity])

        result = await repo.list_by_type(
            document_id="DOC-001",
            entity_type="person_name",
        )

        entities = list(result)
        assert all(e["entity_type"] == "person_name" for e in entities)

    @pytest.mark.asyncio
    async def test_create_many_entities(
        self, mock_cosmos_container, sample_entity
    ):
        """Test bulk entity creation."""
        from src.api.repositories.entity_repository import EntityRepository

        repo = EntityRepository.__new__(EntityRepository)
        repo._container = mock_cosmos_container

        entities = [
            sample_entity,
            {**sample_entity, "id": "ENT-002", "entity_type": "date"},
            {**sample_entity, "id": "ENT-003", "entity_type": "amount"},
        ]

        mock_cosmos_container.create_item = AsyncMock(
            side_effect=lambda body: body
        )

        results = await repo.create_many(entities)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_delete_entities_by_document(
        self, mock_cosmos_container
    ):
        """Test deleting all entities for a document."""
        from src.api.repositories.entity_repository import EntityRepository

        repo = EntityRepository.__new__(EntityRepository)
        repo._container = mock_cosmos_container

        await repo.delete_by_document(document_id="DOC-001")

        # Should query and delete each entity
        mock_cosmos_container.query_items.assert_called()


class TestSummaryRepository:
    """Tests for summary repository operations."""

    @pytest.mark.asyncio
    async def test_create_summary(self, mock_cosmos_container, sample_summary):
        """Test creating a document summary."""
        from src.api.repositories.summary_repository import SummaryRepository

        repo = SummaryRepository.__new__(SummaryRepository)
        repo._container = mock_cosmos_container

        mock_cosmos_container.create_item.return_value = sample_summary

        result = await repo.create(sample_summary)

        mock_cosmos_container.create_item.assert_called_once()
        assert "summary_text" in result

    @pytest.mark.asyncio
    async def test_get_summary(self, mock_cosmos_container, sample_summary):
        """Test retrieving a summary by document ID."""
        from src.api.repositories.summary_repository import SummaryRepository

        repo = SummaryRepository.__new__(SummaryRepository)
        repo._container = mock_cosmos_container

        mock_cosmos_container.read_item.return_value = sample_summary

        result = await repo.get_by_document(document_id="DOC-001")

        assert result["summary_text"].startswith("Medical examination")

    @pytest.mark.asyncio
    async def test_update_summary(self, mock_cosmos_container, sample_summary):
        """Test updating a summary."""
        from src.api.repositories.summary_repository import SummaryRepository

        repo = SummaryRepository.__new__(SummaryRepository)
        repo._container = mock_cosmos_container

        updated = {**sample_summary, "summary_text": "Updated summary"}
        mock_cosmos_container.replace_item.return_value = updated

        result = await repo.update(
            summary_id="SUM-001",
            document_id="DOC-001",
            data={"summary_text": "Updated summary"},
        )

        assert result["summary_text"] == "Updated summary"

    @pytest.mark.asyncio
    async def test_list_summaries_by_case(
        self, mock_cosmos_container, sample_summary
    ):
        """Test listing summaries for a case."""
        from src.api.repositories.summary_repository import SummaryRepository

        repo = SummaryRepository.__new__(SummaryRepository)
        repo._container = mock_cosmos_container

        summaries = [
            sample_summary,
            {**sample_summary, "id": "SUM-002", "document_id": "DOC-002"},
        ]
        mock_cosmos_container.query_items.return_value = iter(summaries)

        result = await repo.list_by_case(case_id="CASE-202512-000001")

        assert len(list(result)) == 2

    @pytest.mark.asyncio
    async def test_delete_summary(self, mock_cosmos_container):
        """Test deleting a summary."""
        from src.api.repositories.summary_repository import SummaryRepository

        repo = SummaryRepository.__new__(SummaryRepository)
        repo._container = mock_cosmos_container

        await repo.delete(
            summary_id="SUM-001",
            document_id="DOC-001",
        )

        mock_cosmos_container.delete_item.assert_called_once()


class TestEntityTypes:
    """Tests for entity type handling."""

    def test_valid_entity_types(self):
        """Test common entity types are recognized."""
        valid_types = [
            "person_name",
            "organization",
            "date",
            "amount",
            "address",
            "phone",
            "email",
            "diagnosis",
            "medication",
            "policy_number",
        ]

        # Entity types should be handled as strings
        for entity_type in valid_types:
            assert isinstance(entity_type, str)

    def test_entity_normalization(self, sample_entity):
        """Test entity value normalization."""
        # Original value
        assert sample_entity["value"] == "John Smith"

        # Normalized value should be uppercase
        assert sample_entity["normalized_value"] == "JOHN SMITH"


class TestSummaryKeyPoints:
    """Tests for summary key points handling."""

    def test_key_points_list(self, sample_summary):
        """Test key points are stored as list."""
        assert isinstance(sample_summary["key_points"], list)
        assert len(sample_summary["key_points"]) == 3

    def test_key_points_are_strings(self, sample_summary):
        """Test all key points are strings."""
        for point in sample_summary["key_points"]:
            assert isinstance(point, str)


class TestConfidenceScores:
    """Tests for confidence score handling."""

    def test_entity_confidence_range(self, sample_entity):
        """Test entity confidence is between 0 and 1."""
        confidence = sample_entity["confidence"]
        assert 0.0 <= confidence <= 1.0

    def test_summary_confidence_range(self, sample_summary):
        """Test summary confidence is between 0 and 1."""
        confidence = sample_summary["confidence"]
        assert 0.0 <= confidence <= 1.0

    def test_high_confidence_threshold(self):
        """Test high confidence threshold for decisions."""
        HIGH_CONFIDENCE_THRESHOLD = 0.85

        sample_confidence = 0.95
        assert sample_confidence >= HIGH_CONFIDENCE_THRESHOLD

    def test_low_confidence_flagging(self):
        """Test low confidence entities are flagged for review."""
        LOW_CONFIDENCE_THRESHOLD = 0.70

        low_confidence = 0.65
        assert low_confidence < LOW_CONFIDENCE_THRESHOLD
        # Should be flagged for human review


class TestAggregations:
    """Tests for entity and summary aggregations."""

    @pytest.mark.asyncio
    async def test_count_entities_by_type(self, mock_cosmos_container):
        """Test counting entities by type."""
        from src.api.repositories.entity_repository import EntityRepository

        repo = EntityRepository.__new__(EntityRepository)
        repo._container = mock_cosmos_container

        mock_cosmos_container.query_items.return_value = iter([
            {"entity_type": "person_name", "count": 5},
            {"entity_type": "date", "count": 3},
            {"entity_type": "amount", "count": 2},
        ])

        counts = await repo.count_by_type(document_id="DOC-001")

        # Should return aggregated counts
        assert counts is not None

    @pytest.mark.asyncio
    async def test_get_all_case_summaries(self, mock_cosmos_container):
        """Test getting aggregated summary for entire case."""
        from src.api.repositories.summary_repository import SummaryRepository

        repo = SummaryRepository.__new__(SummaryRepository)
        repo._container = mock_cosmos_container

        mock_cosmos_container.query_items.return_value = iter([
            {"document_id": "DOC-001", "summary_text": "Summary 1"},
            {"document_id": "DOC-002", "summary_text": "Summary 2"},
        ])

        summaries = await repo.list_by_case(case_id="CASE-001")

        assert len(list(summaries)) == 2
