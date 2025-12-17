# Contributing to HSBC Insurance Underwriting Automation Platform

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [UV](https://github.com/astral-sh/uv) package manager
- Git

### Initial Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd HSBC_IWPB_UW
   ```

2. Install UV (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Install dependencies:
   ```bash
   uv sync --all-extras
   ```

4. Set up environment:
   ```bash
   cp .env.example .env.dev
   # Edit .env.dev with your configuration
   ```

## Development Workflow

### Creating a New Feature

1. **Create a feature specification** in `specs/`:
   ```bash
   mkdir specs/###-feature-name
   # Follow the specification template
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b ###-feature-name
   ```

3. **Implement the feature** following the architecture guidelines

4. **Write tests** for your changes

5. **Run validation**:
   ```bash
   python3 scripts/validate_structure.py
   python3 scripts/check_naming.py
   uv run pytest
   uv run import-linter
   ```

### Code Style

- **Python**: Follow PEP 8 style guide
- **Naming**: Use snake_case for all directories and files
- **Type Hints**: Include type hints for all function signatures
- **Docstrings**: Use Google-style docstrings for all public functions

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test suite
uv run pytest test/unit/
uv run pytest test/integration/
uv run pytest test/e2e/

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Pre-commit Validation

Before committing, ensure:
1. All tests pass
2. Structure validation passes
3. Naming conventions are followed
4. Import layering is correct

```bash
# Validation checklist
python3 scripts/validate_structure.py && \
python3 scripts/check_naming.py && \
uv run pytest && \
uv run import-linter
```

## Project Structure Guidelines

### Directory Naming
- All directories MUST use `snake_case` naming
- Example: `document_classification`, not `DocumentClassification` or `document-classification`

### Component Structure
Each component should have:
```
src/component_name/
├── __init__.py           # Module exports
├── main_module.py        # Primary implementation
├── config.py            # Component configuration
├── pyproject.toml       # Component dependencies
└── README.md            # Component documentation
```

### Interface Implementation
Components must implement interfaces from `src/interfaces/`:
```python
from src.interfaces.processor import IDocumentProcessor

class MyComponent:
    """Implements IDocumentProcessor"""
    
    def process(self, document: dict) -> dict:
        # Implementation
        pass
```

### Dependency Management
- Add shared dependencies to root `pyproject.toml`
- Add component-specific dependencies to component's `pyproject.toml`
- Use `uv sync` to update dependencies

## Testing Guidelines

### Test Organization
- **Unit tests**: `test/unit/component_name/`
- **Integration tests**: `test/integration/`
- **E2E tests**: `test/e2e/`
- **Test utilities**: `test/test_utils/`

### Test Naming
- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Writing Tests
```python
def test_classifier_classifies_document():
    """Test that classifier correctly classifies a document."""
    # Arrange
    classifier = DocumentClassifier()
    document = create_mock_document()
    
    # Act
    result = classifier.classify(document)
    
    # Assert
    assert result["document_type"] == "policy_application"
    assert result["confidence"] > 0.9
```

## Documentation Guidelines

### Code Documentation
- All public functions must have docstrings
- Use Google-style docstrings
- Include type hints in function signatures

Example:
```python
def process_document(
    document: dict[str, Any],
    options: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    Process a document through the classification pipeline.
    
    Args:
        document: Document object with id, name, content fields
        options: Optional processing options
        
    Returns:
        Processing results with classification and confidence
        
    Raises:
        ProcessingError: If document processing fails
    """
    pass
```

### Architecture Decisions
Document significant architectural decisions in `docs/adr/`:
```markdown
# ADR ###: Title

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Deprecated
**Deciders**: Team Name

## Context
[Describe the context and problem]

## Decision
[Describe the decision]

## Consequences
[Describe consequences: positive, negative, mitigation]
```

## Pull Request Process

1. **Create a feature branch** from `main`
2. **Implement changes** following guidelines above
3. **Write/update tests** for your changes
4. **Update documentation** as needed
5. **Run validation** to ensure all checks pass
6. **Create pull request** with:
   - Clear description of changes
   - Link to related specification (if applicable)
   - Test results
   - Any breaking changes noted

### PR Checklist
- [ ] Tests pass locally
- [ ] Structure validation passes
- [ ] Naming conventions followed
- [ ] Import layering correct
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)

## Component Development

### Adding a New Component

1. Create component directory:
   ```bash
   mkdir src/new_component
   ```

2. Create component files:
   ```bash
   touch src/new_component/__init__.py
   touch src/new_component/component.py
   touch src/new_component/config.py
   ```

3. Create component `pyproject.toml`:
   ```toml
   [project]
   name = "hsbc-new-component"
   version = "0.1.0"
   requires-python = ">=3.11"
   dependencies = [
       # Component-specific dependencies
   ]
   ```

4. Create component tests:
   ```bash
   mkdir test/unit/new_component
   touch test/unit/new_component/test_component.py
   ```

5. Create component README:
   ```bash
   touch src/new_component/README.md
   ```

6. Register with root workspace:
   Edit root `pyproject.toml` to add component to `[tool.uv.workspace.members]`

## Questions or Issues?

- Check existing documentation in `docs/`
- Review Architecture Decision Records in `docs/adr/`
- Consult the quickstart guide in `docs/guides/quickstart.md`
- Open an issue for questions or problems

## License

Copyright © 2025 HSBC. All rights reserved.
