# Testing Strategy

This document outlines the testing approach for the Contoso Bank Insurance Underwriting Automation Platform monorepo.

## Testing Philosophy

Our testing strategy follows these principles:

1. **Test at appropriate levels**: Unit tests for components, integration tests for workflows, E2E tests for complete scenarios
2. **Maintain separation**: Tests are completely separated from source code (FR-007)
3. **Mirror structure**: Test organization mirrors source structure for easy navigation
4. **Enable TDD**: Test infrastructure supports test-driven development
5. **Ensure quality**: Automated validation in CI/CD pipeline

## Test Organization

```
test/
├── unit/                          # Unit tests (fast, isolated)
│   ├── document_classification/   # Tests for classification component
│   ├── entity_extraction/         # Tests for extraction component
│   ├── document_summarization/    # Tests for summarization component
│   └── shared/                    # Tests for shared utilities
├── integration/                   # Integration tests (component interactions)
│   └── test_orchestration.py     # Tests for workflow orchestration
├── e2e/                          # End-to-end tests (complete workflows)
│   ├── test_document_processing_workflow.py
│   └── fixtures/                 # Test data and fixtures
└── test_utils/                   # Shared test utilities
    ├── helpers.py                # Common test helpers
    └── mocks/                    # Mock objects and factories
```

## Test Types

### Unit Tests

**Purpose**: Test individual functions, classes, and modules in isolation

**Location**: `test/unit/[component_name]/`

**Characteristics**:
- Fast execution (< 1 second each)
- No external dependencies (databases, APIs, file system)
- Use mocks and stubs for dependencies
- High code coverage (target: 80%+)

**Example**:
```python
# test/unit/shared/test_file_helpers.py
import pytest
from shared.utils.file_helpers import get_file_extension, validate_file_path

def test_get_file_extension_pdf():
    """Test that PDF extension is correctly extracted."""
    assert get_file_extension("document.pdf") == ".pdf"

def test_get_file_extension_no_extension():
    """Test handling of files without extension."""
    assert get_file_extension("README") == ""

def test_validate_file_path_valid():
    """Test validation of valid file paths."""
    assert validate_file_path("/valid/path/file.txt") is True

def test_validate_file_path_invalid():
    """Test rejection of invalid file paths."""
    with pytest.raises(ValueError):
        validate_file_path("../../etc/passwd")
```

### Integration Tests

**Purpose**: Test interactions between multiple components

**Location**: `test/integration/`

**Characteristics**:
- Medium execution time (1-10 seconds each)
- May use test databases or mock external services
- Test component communication through interfaces
- Validate workflow orchestration

**Example**:
```python
# test/integration/test_orchestration.py
import pytest
from orchestration.workflow import WorkflowOrchestrator
from orchestration.registry import ComponentRegistry

def test_component_registration_and_retrieval():
    """Test that components can be registered and retrieved."""
    registry = ComponentRegistry()
    registry.register_component("classifier", MockClassifier())
    
    classifier = registry.get_component("classifier")
    assert classifier is not None

def test_workflow_execution_with_multiple_components():
    """Test workflow executing multiple components."""
    orchestrator = WorkflowOrchestrator()
    orchestrator.add_step("classify", ClassifyStep())
    orchestrator.add_step("extract", ExtractStep())
    
    result = orchestrator.execute(test_document)
    assert result.status == "completed"
```

### End-to-End Tests

**Purpose**: Test complete user workflows from start to finish

**Location**: `test/e2e/`

**Characteristics**:
- Slower execution (10+ seconds each)
- Use real or test Azure services
- Test complete business scenarios
- Validate HITL workflows

**Example**:
```python
# test/e2e/test_document_processing_workflow.py
import pytest
from pathlib import Path

@pytest.mark.e2e
def test_complete_document_processing():
    """Test complete workflow from upload to summary."""
    # Given: A policy document
    document = load_test_document("sample_policy.pdf")
    
    # When: Document is uploaded and processed
    upload_response = upload_document(document)
    classification = classify_document(upload_response.document_id)
    entities = extract_entities(upload_response.document_id)
    summary = summarize_document(upload_response.document_id)
    
    # Then: All steps complete successfully
    assert classification.document_type == "policy"
    assert len(entities) > 0
    assert summary.length > 100
```

## Testing Conventions

### File Naming

- Unit tests: `test_[module_name].py`
- Integration tests: `test_[feature_name].py`
- E2E tests: `test_[workflow_name].py`
- Test classes: `Test[ClassName]`
- Test functions: `test_[what_is_being_tested]`

### Test Structure (AAA Pattern)

All tests should follow the Arrange-Act-Assert pattern:

```python
def test_function_name():
    """Clear description of what is being tested."""
    # Arrange: Set up test data and preconditions
    input_data = create_test_data()
    expected_output = "expected_result"
    
    # Act: Execute the function being tested
    actual_output = function_under_test(input_data)
    
    # Assert: Verify the result
    assert actual_output == expected_output
```

### Fixtures

Use pytest fixtures for reusable test setup:

```python
# test/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def test_data_dir():
    """Provide path to test data directory."""
    return Path(__file__).parent / "test_utils" / "fixtures"

@pytest.fixture
def sample_document(test_data_dir):
    """Provide sample document for testing."""
    return (test_data_dir / "sample.pdf").read_bytes()
```

## Running Tests

### Run All Tests

```bash
uv run pytest test/
```

### Run Specific Test Types

```bash
# Unit tests only
uv run pytest test/unit/

# Integration tests only
uv run pytest test/integration/

# E2E tests only
uv run pytest test/e2e/
```

### Run Tests with Coverage

```bash
uv run pytest test/ --cov=src --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```

### Run Tests for Specific Component

```bash
uv run pytest test/unit/document_classification/
```

### Run Tests in Watch Mode

```bash
uv run pytest-watch test/
```

## Test Utilities

### Helper Functions

Located in `test/test_utils/helpers.py`:

```python
from test_utils.helpers import (
    create_mock_document,
    create_mock_entity,
    assert_valid_document
)

def test_with_helpers():
    doc = create_mock_document(filename="test.pdf")
    assert_valid_document(doc)
```

### Mock Objects

Located in `test/test_utils/mocks/`:

```python
from test_utils.mocks.classifier import MockClassifier
from test_utils.mocks.extractor import MockExtractor

def test_with_mocks():
    classifier = MockClassifier(success_rate=0.9)
    result = classifier.classify(document)
```

### Test Fixtures

Located in `test/e2e/fixtures/`:

- Sample documents (PDFs, images)
- Expected outputs
- Configuration templates

## Code Coverage

### Coverage Goals

- **Unit tests**: 80%+ coverage
- **Integration tests**: 60%+ coverage
- **Critical paths**: 100% coverage
  - Authentication/authorization
  - Data validation
  - Error handling

### Measuring Coverage

```bash
# Generate coverage report
uv run pytest test/ --cov=src --cov-report=term --cov-report=html

# View coverage by module
uv run pytest test/ --cov=src --cov-report=term-missing
```

### Excluding from Coverage

Add to `pyproject.toml`:

```toml
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/test_utils/*",
    "*/__init__.py"
]
```

## Mocking External Services

### Azure Services

Use mocks for Azure services in unit and integration tests:

```python
from unittest.mock import Mock, patch

@patch('azure.ai.formrecognizer.DocumentAnalysisClient')
def test_with_azure_mock(mock_client):
    mock_client.begin_analyze_document.return_value = mock_response
    result = extract_entities(document)
    assert result is not None
```

### Environment Variables

Use pytest-env or monkeypatch for environment variables:

```python
def test_with_env_vars(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.endpoint")
    config = EnvironmentConfig.load(".env.dev")
    assert config.get("AZURE_OPENAI_ENDPOINT") == "https://test.endpoint"
```

## Test Data Management

### Test Data Location

- Unit test data: Inline or in test files
- Integration test data: `test/integration/fixtures/`
- E2E test data: `test/e2e/fixtures/`

### Test Data Guidelines

1. **Use realistic data**: Test data should resemble production data
2. **Sanitize sensitive data**: Remove PII, credentials, etc.
3. **Keep data small**: Minimize test data size for fast execution
4. **Version control**: Commit test data to repository
5. **Document data**: Include README explaining test data purpose

## Troubleshooting

### Tests Hanging

- Check for infinite loops or blocking I/O
- Use pytest timeout: `pytest --timeout=30`
- Review external service calls

### Flaky Tests

- Identify non-deterministic behavior
- Use fixtures for consistent state
- Mock time-dependent operations
- Add retry logic for external services

### Coverage Gaps

- Run coverage with `--cov-report=term-missing`
- Identify uncovered lines
- Add tests for critical paths first
- Use mutation testing for quality validation

## Best Practices

1. **Write tests first** (TDD): Define expected behavior before implementation
2. **One assertion per test**: Focus on testing one thing
3. **Use descriptive names**: Test name should describe what it tests
4. **Keep tests independent**: Tests should not depend on each other
5. **Mock external dependencies**: Don't test external services
6. **Test edge cases**: Cover boundary conditions and error cases
7. **Maintain test quality**: Apply same standards as production code
8. **Review test failures**: Don't ignore failing tests

## Related Documentation

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Component Testing Guide](./component_testing.md)
- [ADR-005: Testing Strategy](../adr/005-testing-strategy.md)

## Support

For questions about testing:
- Review [CONTRIBUTING.md](../../CONTRIBUTING.md)
- Consult the QA team
- Check CI/CD logs for test failures
