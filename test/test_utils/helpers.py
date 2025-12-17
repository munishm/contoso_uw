"""Test helper functions for shared use across test suites."""

from pathlib import Path
from typing import Any, Optional


def create_mock_document(
    doc_id: str = "test-doc-001",
    name: str = "test_document.pdf",
    content_type: str = "application/pdf",
    size_bytes: int = 1024
) -> dict[str, Any]:
    """
    Create a mock document object for testing.
    
    Args:
        doc_id: Document ID
        name: Document name
        content_type: MIME type
        size_bytes: File size
        
    Returns:
        Mock document dictionary
    """
    return {
        "id": doc_id,
        "name": name,
        "content_type": content_type,
        "size_bytes": size_bytes,
        "created_at": "2025-12-15T10:00:00Z",
        "metadata": {}
    }


def create_mock_entity(
    entity_type: str = "policy_number",
    value: str = "POL-12345",
    confidence: float = 0.95
) -> dict[str, Any]:
    """
    Create a mock entity object for testing.
    
    Args:
        entity_type: Type of entity
        value: Entity value
        confidence: Confidence score
        
    Returns:
        Mock entity dictionary
    """
    return {
        "type": entity_type,
        "value": value,
        "confidence": confidence,
        "start": 0,
        "end": len(value),
        "metadata": {}
    }


def get_test_data_path(filename: str) -> Path:
    """
    Get path to test data file.
    
    Args:
        filename: Name of test data file
        
    Returns:
        Path to test data file
    """
    return Path(__file__).parent.parent / "e2e" / "fixtures" / filename


def assert_valid_document(doc: dict[str, Any]) -> None:
    """
    Assert document has required fields.
    
    Args:
        doc: Document dictionary to validate
        
    Raises:
        AssertionError: If document is invalid
    """
    required_fields = ["id", "name", "content_type", "size_bytes", "created_at"]
    for field in required_fields:
        assert field in doc, f"Document missing required field: {field}"


def assert_valid_entity(entity: dict[str, Any]) -> None:
    """
    Assert entity has required fields.
    
    Args:
        entity: Entity dictionary to validate
        
    Raises:
        AssertionError: If entity is invalid
    """
    required_fields = ["type", "value", "confidence", "start", "end"]
    for field in required_fields:
        assert field in entity, f"Entity missing required field: {field}"
    
    assert 0.0 <= entity["confidence"] <= 1.0, "Confidence must be between 0 and 1"
    assert entity["start"] >= 0, "Start position must be non-negative"
    assert entity["end"] >= entity["start"], "End must be >= start"
