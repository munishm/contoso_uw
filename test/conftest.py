# pytest configuration
import pytest
import sys
from pathlib import Path

# Add src to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_document():
    """Fixture providing a sample document for testing."""
    return {
        "id": "test-doc-001",
        "name": "test_document.pdf",
        "content": "Sample document content for testing",
        "metadata": {
            "type": "application/pdf",
            "size": 1024,
            "created_at": "2025-12-15T00:00:00Z"
        }
    }


@pytest.fixture
def sample_entity():
    """Fixture providing a sample entity for testing."""
    return {
        "type": "policy_number",
        "value": "POL-12345",
        "confidence": 0.95,
        "start": 0,
        "end": 9
    }


@pytest.fixture
def mock_azure_client():
    """Fixture providing a mock Azure client."""
    class MockAzureClient:
        def __init__(self):
            self.calls = []
        
        def call_api(self, *args, **kwargs):
            self.calls.append({"args": args, "kwargs": kwargs})
            return {"status": "success", "data": "mock_response"}
    
    return MockAzureClient()
