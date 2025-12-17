# ADR 002: Component Interface Contracts

**Date**: 2025-12-15  
**Status**: Accepted  
**Deciders**: Platform Team  

## Context

Components must be pluggable and interchangeable to support different use cases and implementations. We need a mechanism to ensure components can communicate reliably without tight coupling.

Key requirements:
- Components should be swappable without modifying other components
- Type safety to catch errors at development time
- Clear contracts for what each component provides
- Version compatibility management

## Decision

We will use **Python Protocol classes** for interface definitions located in `src/interfaces/`:

```python
from typing import Protocol

class IDocumentProcessor(Protocol):
    def process(self, document: dict) -> dict:
        ...
    
    def get_supported_types(self) -> list[str]:
        ...
```

**Key Decisions**:
1. **Python Protocols**: Use Protocol for structural typing (duck typing with type hints)
2. **Centralized Interfaces**: All interfaces in `src/interfaces/` directory
3. **Version Suffixes**: Interfaces versioned with suffixes (e.g., `IClassifierV1`, `IClassifierV2`)
4. **JSON Schemas**: Complement Protocols with JSON schemas for data validation

## Consequences

### Positive
- Static type checking with mypy catches interface violations early
- Components remain loosely coupled through interface contracts
- Clear documentation of what each component must implement
- Versioning strategy prevents breaking changes
- JSON schemas enable runtime validation and multi-language support

### Negative
- Python Protocols not enforced at runtime (need validation)
- Learning curve for developers unfamiliar with Protocol pattern
- More boilerplate code compared to dynamic typing

### Mitigation
- Comprehensive documentation with examples
- Validation layer to check interface compliance at runtime
- Import-linter to enforce that components only depend on interfaces

## Alternatives Considered

1. **Abstract Base Classes (ABC)**: Use ABC instead of Protocol
   - Rejected: Requires explicit inheritance, tighter coupling than Protocols

2. **No Formal Interfaces**: Rely on duck typing
   - Rejected: No type safety, harder to understand contracts

3. **gRPC/Protobuf**: Define interfaces with protobuf
   - Rejected: Overkill for POC, adds complexity for in-process communication

## Implementation Details

Directory structure:
```
src/interfaces/
├── __init__.py
├── processor.py      # IDocumentProcessor base interface
├── classifier.py     # IClassifier interface
├── extractor.py      # IEntityExtractor interface
├── summarizer.py     # ISummarizer interface
└── schemas/
    └── *.json        # JSON schemas for data validation
```

Components implement interfaces:
```python
class DocumentClassifier:
    """Implements IClassifier"""
    
    def classify(self, document: dict) -> dict:
        # Implementation
        pass
```

## References

- [Research Findings](../../specs/001-project-structure/research.md#research-task-1-component-interface-definition)
- [Python Protocols (PEP 544)](https://peps.python.org/pep-0544/)
