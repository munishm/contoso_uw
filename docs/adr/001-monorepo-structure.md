# ADR 001: Monorepo Structure

**Date**: 2025-12-15  
**Status**: Accepted  
**Deciders**: Platform Team  

## Context

We need to establish a directory structure for the Contoso Bank Insurance Underwriting Automation Platform that supports:
- Multiple pluggable components that can be independently developed and deployed
- Shared utilities and models across components
- Clear separation between source code, tests, and documentation
- Environment-specific configuration management

The structure must enable efficient development while maintaining clarity and preventing code duplication.

## Decision

We will use a **monorepo structure** with the following organization:

```
CONTOSO_IWPB_UW/
├── src/                    # All component source code
│   ├── interfaces/        # Component contracts
│   ├── shared/            # Shared utilities
│   └── [components]/      # Individual components
├── test/                  # All tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                  # Documentation
└── specs/                 # Feature specifications
```

**Key Decisions**:
1. **Monorepo vs Multi-repo**: Monorepo chosen for easier cross-component refactoring and unified CI/CD
2. **Top-level src/**: All components under single source directory for clarity
3. **Snake case naming**: All directories use `snake_case` for consistency
4. **Separate test directory**: Tests separated from source (not co-located) for cleaner structure
5. **Per-component dependencies**: Each component has own `pyproject.toml` for independent versioning

## Consequences

### Positive
- Single repository simplifies onboarding and cross-component changes
- Clear structure makes it obvious where code belongs
- Snake case naming provides consistency across the codebase
- Separation of tests enables focused tooling and faster test execution
- Per-component dependencies enable independent deployment

### Negative
- Larger repository size compared to multi-repo approach
- Requires discipline to maintain boundaries between components
- All developers have access to all code (may be security concern for some orgs)

### Mitigation
- Use import-linter to enforce component boundaries
- Implement pre-commit hooks for validation
- Clear documentation on component organization
- Regular structure validation in CI/CD

## Alternatives Considered

1. **Multi-repo Architecture**: Each component in separate repository
   - Rejected: Too much overhead for POC phase, harder to refactor across components

2. **Feature-based Structure**: Organize by features instead of technical layers
   - Rejected: Doesn't align with plug-and-play component requirement

3. **Flat Structure**: All components at root level
   - Rejected: Doesn't scale, unclear separation of concerns

## References

- [Feature Specification](../../specs/001-project-structure/spec.md)
- [Implementation Plan](../../specs/001-project-structure/plan.md)
- [Research Findings](../../specs/001-project-structure/research.md)
