# Research: Basic Project Structure

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)  
**Created**: 15 December 2025  
**Status**: Complete

## Purpose

This document resolves all NEEDS CLARIFICATION items from Technical Context and addresses remaining underspecified areas identified in [underspecified-areas.md](underspecified-areas.md). Research findings inform the design decisions in Phase 1.

---

## Research Task 1: Component Interface Definition

**Context**: FR-015 requires "clearly defined" interfaces for plug-and-play functionality. Need to determine how component interfaces should be structured.

### Findings

**Industry Best Practices**:
- **Contracts/Interfaces Directory**: Successful monorepos (Google, Microsoft, Nx) use dedicated interfaces/ or contracts/ directories
- **API-First Design**: OpenAPI/AsyncAPI specs enable contract-first development
- **Type Safety**: TypeScript interfaces or Python Protocols provide compile-time guarantees
- **Versioning**: Semantic versioning in interface contracts prevents breaking changes

**Recommendation for Contoso Project**:
```
src/
├── interfaces/                 # Component interaction contracts
│   ├── document_processor.py  # Base interface for all doc processors
│   ├── classifier.py           # Classification component interface
│   └── schemas/
│       └── document_schema.json  # Shared data schemas
```

**Decision**:
- Create `src/interfaces/` directory containing Python Protocol classes
- Use JSON schemas in `src/interfaces/schemas/` for data contracts
- Each component MUST implement interfaces defined here
- Interface versioning through semantic versioning (e.g., IClassifierV1, IClassifierV2)

**Rationale**:
- Central location ensures all teams reference same contracts
- Python Protocols provide runtime and static type checking
- JSON schemas enable multi-language validation (Python, TypeScript, etc.)
- Aligns with Principle 8 (Reusable Patterns & Extensibility)

---

## Research Task 2: Component Communication Patterns

**Context**: Edge case raised about component-to-component communication. Need architectural pattern.

### Findings

**Pattern Analysis**:

1. **Direct Component Calls** (Tight Coupling)
   - ✅ Simple, minimal overhead
   - ❌ Creates dependencies, hard to swap implementations
   - ❌ Violates plug-and-play requirement

2. **Event Bus / Pub-Sub** (Loose Coupling)
   - ✅ Decoupled, easy to add/remove components
   - ✅ Supports async processing
   - ❌ Adds complexity, harder to debug
   - ❌ Overkill for POC phase

3. **Orchestrator Pattern** (Centralized Control)
   - ✅ Clear workflow visibility
   - ✅ Easy to modify pipelines
   - ✅ Fits HITL requirements (humans monitor central orchestrator)
   - ✅ Aligns with LangGraph patterns if used
   - ❌ Orchestrator can become bottleneck

4. **Repository + Dependency Injection** (Flexible)
   - ✅ Components registered at runtime
   - ✅ Easy to swap implementations
   - ✅ Testable (mock components)
   - ❌ Requires DI framework

**Recommendation for Contoso Project**:

**POC Phase**: Orchestrator Pattern with Interface Contracts
- Central workflow orchestrator in `src/orchestration/workflow.py`
- Components communicate via orchestrator, not directly
- Orchestrator injects dependencies per workflow step
- Aligns with LangGraph state machines if adopted

**Production**: Consider Event Bus for Scalability
- Azure Service Bus or Event Grid for async workflows
- Components subscribe to events (document.uploaded, entity.extracted)
- Enables horizontal scaling and resilience

```
src/
├── orchestration/
│   ├── workflow.py        # Central orchestrator
│   ├── registry.py        # Component registration
│   └── pipeline.py        # Workflow definitions
├── interfaces/            # Component contracts
└── [components]/          # Implementations
```

**Decision**: Use Orchestrator Pattern for POC with interface-based component registration.

**Rationale**:
- Simplifies POC development while maintaining flexibility
- Enables plug-and-play through component registry
- Supports HITL by centralizing control flow
- Can migrate to event bus in production without changing component interfaces

---

## Research Task 3: Monorepo Tooling Integration

**Context**: Per-component dependencies (FR-013) require workspace management. Need to select tooling.

### Findings

**Tooling Options**:

1. **npm/yarn/pnpm Workspaces** (JavaScript/TypeScript)
   - ✅ Native to npm ecosystem
   - ✅ Dependency hoisting
   - ✅ Link local packages
   - ❌ JavaScript-centric

2. **Lerna** (JavaScript/Multi-language)
   - ✅ Manages versioning across packages
   - ✅ Runs scripts across workspaces
   - ❌ Less actively maintained
   - ❌ Overhead for simple structures

3. **Nx** (Multi-language, Enterprise-grade)
   - ✅ Supports Python, Node.js, etc.
   - ✅ Advanced caching and task orchestration
   - ✅ Dependency graph visualization
   - ✅ Scales to large monorepos
   - ❌ Steeper learning curve
   - ❌ Configuration overhead

4. **Poetry (Python) + npm Workspaces (Node.js)** (Hybrid)
   - ✅ Best-of-breed for each language
   - ✅ Poetry handles Python dependencies elegantly
   - ✅ npm workspaces for any Node.js tooling
   - ❌ Two tools to learn

5. **Manual Management** (No tooling)
   - ✅ Simple, no dependencies
   - ❌ No automatic linking
   - ❌ Doesn't scale

**Python Component Dependency Management**:
- **UV**: Modern, extremely fast, handles virtual envs, lockfiles, dependency resolution
- **Poetry**: Popular but slower than UV
- **pip + requirements.txt**: Manual but universally understood

**Recommendation for Contoso Project**:

**For Python-Heavy Monorepo**:
- **Primary**: UV workspaces (UV supports monorepo workspaces natively)
- **Structure**:
  ```
  /
  ├── pyproject.toml           # Root workspace config
  ├── uv.lock                  # Root lockfile
  ├── src/
  │   ├── component_a/
  │   │   └── pyproject.toml   # Component-specific dependencies
  │   └── component_b/
  │       └── pyproject.toml
  ```
- **Rationale**: Azure AI SDK is Python-based, UV is extremely fast and modern

**If Multi-Language (Python + Node.js tooling)**:
- Hybrid: UV for Python + npm workspaces for Node.js
- Or: Nx for unified experience (worth evaluation)

**Decision**: Use **UV Workspaces** for Python monorepo with optional npm workspaces if Node.js tooling needed (e.g., frontend, build tools).

**Rationale**:
- Aligns with Azure AI Python SDK ecosystem
- UV provides extremely fast dependency resolution (10-100x faster than pip/poetry)
- Native workspace support for monorepos
- Supports per-component pyproject.toml (FR-013 requirement)
- Can add npm workspaces later without restructuring

---

## Research Task 4: Shared Resource Organization

**Context**: FR-006 mentions shared/ and common/ but unclear if both needed and how to organize.

### Findings

**Naming Conventions**:
- **shared/**: General-purpose utilities used by many components
- **common/**: Domain-specific shared code (insurance-specific)
- **lib/**: External libraries or vendored code
- **core/**: Essential infrastructure (logging, config, etc.)

**Organization Patterns**:

1. **Flat shared/ directory**
   - ✅ Simple
   - ❌ Doesn't scale past ~20 files

2. **Organized by type (shared/utils/, shared/models/)**
   - ✅ Clear separation
   - ✅ Scales well
   - ❌ Technical organization vs domain

3. **Organized by domain (shared/insurance/, shared/document/)**
   - ✅ Business-aligned
   - ❌ Can duplicate technical utilities

4. **Hybrid (shared/utils/ + shared/insurance_domain/)**
   - ✅ Best of both worlds
   - ✅ Scales and stays organized

**Recommendation**:

Use **single `shared/` directory** organized by type, with domain-specific subdirectories as needed:

```
src/shared/
├── utils/              # Pure utilities (formatting, validation)
├── models/             # Shared data models (Document, Entity)
├── schemas/            # JSON schemas for data contracts
├── interfaces/         # MOVED: Better at src/interfaces/ (top-level)
├── config/             # Shared configuration utilities
└── insurance_domain/   # Insurance-specific shared logic (if substantial)
```

**Decision**: Single `src/shared/` directory with type-based organization. Move interfaces to `src/interfaces/` for better visibility.

**Rationale**:
- One shared location reduces confusion
- Type-based organization scales to 100+ files
- Interfaces at top level emphasize their importance
- Follows Principle 8 (extensibility through clear organization)

---

## Research Task 5: Test Organization Details

**Context**: test/ organized by type (unit/, e2e/) but component mapping unclear.

### Findings

**Test Organization Patterns**:

1. **Mirror Source Structure**
   ```
   test/unit/
   ├── document_classification/
   │   └── test_classifier.py
   └── entity_extraction/
       └── test_extractor.py
   ```
   - ✅ Easy to locate tests for any source file
   - ✅ Clear 1:1 mapping
   - ✅ Scales well

2. **Flat by Component**
   ```
   test/unit/
   ├── test_document_classification.py
   ├── test_entity_extraction.py
   ```
   - ✅ Simple for small projects
   - ❌ Doesn't scale past ~10 components

3. **Feature-Based**
   ```
   test/unit/
   ├── classification_tests/
   ├── extraction_tests/
   ```
   - ❌ Disconnected from source structure

**Test Utilities & Fixtures**:
- **Option A**: `test/utils/` and `test/fixtures/`
- **Option B**: `test/shared/` (mirrors src/shared/)
- **Option C**: `src/shared/test_utils/` (with source code)

**Integration vs E2E**:
- **Integration tests**: Test multiple components together (API + service layer)
- **E2E tests**: Full workflow tests (upload document → classification → extraction → output)

**Recommendation**:

```
test/
├── unit/                       # Mirror src/ component structure
│   ├── document_classification/
│   │   ├── test_classifier.py
│   │   └── test_models.py
│   ├── entity_extraction/
│   └── shared/
│       └── test_utils.py
│
├── integration/                # Multi-component tests
│   ├── test_classification_to_extraction.py
│   └── test_orchestration.py
│
├── e2e/                        # Full workflow tests
│   ├── test_document_processing_workflow.py
│   └── fixtures/
│       └── sample_documents/
│
├── conftest.py                 # Pytest shared fixtures
└── test_utils/                 # Shared test utilities
    ├── mocks/
    └── helpers.py
```

**Decision**: Mirror source structure in test/unit/, add test/integration/ for multi-component tests, test/e2e/ for workflows, test/test_utils/ for shared test code.

**Rationale**:
- Clear mapping from source to tests
- Separates test types by scope and speed
- Shared test utilities centralized
- Follows Python/pytest conventions

---

## Research Task 6: Circular Dependency Prevention

**Context**: Risk of shared code depending on components creates circular dependencies.

### Findings

**Dependency Layering**:
```
┌─────────────────────┐
│    Components       │  ← Can import from shared, interfaces
│  (src/component_x)  │
└─────────────────────┘
         ↓ imports
┌─────────────────────┐
│   Shared Utilities  │  ← Can import from interfaces only
│   (src/shared)      │
└─────────────────────┘
         ↓ imports
┌─────────────────────┐
│    Interfaces       │  ← No imports from src/
│  (src/interfaces)   │
└─────────────────────┘
```

**Enforcement Tools**:
- **import-linter** (Python): Defines allowed import patterns
- **importchecker** (Python): Validates import rules
- **Pre-commit hooks**: Block commits violating rules
- **CI validation**: Fails build on circular dependencies

**Example Configuration** (import-linter):
```toml
# .import-linter.ini
[importlinter]
root_package = src

[importlinter:contract:layers]
name = Enforce layering
type = layers
layers =
    interfaces
    shared
    components
```

**Decision**: Implement strict layering with import-linter validation in CI.

**Layering Rules**:
1. **interfaces/** cannot import from src/ at all (only stdlib)
2. **shared/** can import from interfaces/ only
3. **Components** can import from shared/ and interfaces/
4. **Components** can import from other components ONLY through interfaces/

**Rationale**:
- Prevents technical debt from circular dependencies
- Enforces clean architecture principles
- Automated enforcement removes human error
- Aligns with Principle 8 (reusable, extensible patterns)

---

## Research Task 7: Build Artifact Organization

**Context**: FR-007 requires separation but monorepo build structure needs definition.

### Findings

**Build Output Patterns**:

1. **Single Root build/ Directory**
   ```
   build/
   ├── document_classification/
   ├── entity_extraction/
   └── dist/
       └── [combined artifacts]
   ```
   - ✅ Simple to clean (`rm -rf build/`)
   - ✅ Clear separation from source
   - ❌ Can mix dev and prod builds

2. **Separate dist/ and build/**
   ```
   build/        # Intermediate files, caches
   dist/         # Final distributables
   ```
   - ✅ Separates intermediate from final
   - ✅ Can gitignore different levels
   - ✅ Clearer intent

3. **Per-Component Build Outputs**
   ```
   src/component_x/
   ├── dist/      # Component-specific build output
   └── .cache/    # Build cache
   ```
   - ✅ Co-locates component with its build
   - ❌ Violates FR-007 (separation from source)
   - ❌ Harder to clean all builds

**Recommendation**:

```
/
├── build/                       # Intermediate build files (gitignored)
│   ├── document_classification/
│   ├── entity_extraction/
│   └── .cache/                 # Build tool caches (e.g., pytest, mypy)
│
└── dist/                        # Final distributable artifacts (gitignored)
    ├── wheels/                  # Python wheel packages
    ├── docker/                  # Docker images exports
    └── packages/                # Versioned component packages
```

**Decision**: Use separate build/ (intermediate) and dist/ (final) directories at repository root.

**Rationale**:
- Clear separation of build stages
- Easy to clean intermediate files vs distributables
- Aligns with Python packaging conventions
- Supports CI/CD artifact collection (dist/ only)

---

## Research Task 8: Version Control Integration Details

**Context**: FR-012 mentions basic exclusions but needs specific patterns.

### Findings

**Essential .gitignore Patterns**:

**Python-Specific**:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
ENV/
env/
.venv

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/

# Type checking
.mypy_cache/
.dmypy.json
dmypy.json
.pytype/
```

**Environment & Secrets**:
```
# Environment files (CRITICAL - FR-004)
.env
.env.dev
.env.staging
.env.prod
.env.local
.env.*.local

# Keep template
!.env.example
```

**IDE & OS**:
```
# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# OS
Thumbs.db
desktop.ini
```

**Azure & Logs**:
```
# Azure
.azure/
*.log
logs/

# Application logs
*.log
logs/
```

**Decision**: Comprehensive .gitignore with security focus.

**Critical Requirements**:
1. ✅ All .env files EXCEPT .env.example
2. ✅ Build outputs (build/, dist/)
3. ✅ Dependencies (node_modules/, __pycache__/)
4. ✅ IDE files (.vscode/, .idea/)
5. ✅ Logs and temporary files

**Rationale**:
- Security: Prevents accidental credential commits (Principle 5)
- Cleanliness: Keeps repo focused on source code
- Collaboration: Avoids IDE config conflicts

---

## Research Task 9: Component Versioning Strategy

**Context**: Pluggable components need version management for compatibility.

### Findings

**Versioning Approaches**:

1. **Monorepo Single Version** (All components same version)
   - ✅ Simple, atomic releases
   - ❌ All components version bumps together
   - ❌ Doesn't reflect independent deployability

2. **Independent Component Versions** (Each component versioned separately)
   - ✅ Reflects true independence
   - ✅ Components evolve at different rates
   - ❌ Dependency management complexity
   - ✅ Aligns with pluggable component requirement

3. **Hybrid** (Major version shared, minor independent)
   - ✅ Indicates compatibility
   - ❌ Complex to manage

**Semantic Versioning for Interfaces**:
- **Major**: Breaking interface changes
- **Minor**: Backward-compatible additions
- **Patch**: Bug fixes, no interface changes

**Recommendation**:

**POC Phase**: Single version for simplicity (v0.1.0, v0.2.0)
- All components advance together
- Reduces cognitive overhead during rapid development

**Production**: Independent component versioning
```python
# src/document_classification/pyproject.toml
[project]
name = "contoso-document-classification"
version = "1.2.3"

# src/entity_extraction/pyproject.toml
[project]
name = "contoso-entity-extraction"
version = "2.0.1"
```

**Interface Versioning**:
- Interfaces in `src/interfaces/` have explicit version suffixes
- Example: `IClassifierV1`, `IClassifierV2`
- Components declare which interface version they implement

**Decision**: Single version for POC, independent versioning for production with interface version contracts.

**Rationale**:
- POC simplicity reduces overhead
- Production independence enables flexible deployment
- Interface versioning prevents compatibility issues
- Aligns with Principle 8 (extensibility)

---

## Summary of Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| **Component Interfaces** | `src/interfaces/` with Python Protocols + JSON schemas | Central contracts, type safety, multi-language support |
| **Component Communication** | Orchestrator pattern for POC | Simplifies development, enables HITL, migration path to event bus |
| **Monorepo Tooling** | UV workspaces (Python) | Native to Azure AI SDK ecosystem, extremely fast (10-100x), native workspace support |
| **Shared Resources** | `src/shared/` organized by type | Single location, scalable organization |
| **Test Organization** | Mirror structure in test/unit/, separate integration/ and e2e/ | Clear mapping, scales well, separation by scope |
| **Circular Dependencies** | Strict layering with import-linter | Automated enforcement, prevents tech debt |
| **Build Artifacts** | Separate build/ (intermediate) and dist/ (final) | Clear stages, aligns with Python conventions |
| **Version Control** | Comprehensive .gitignore with security focus | Protects secrets, keeps repo clean |
| **Component Versioning** | Single version for POC, independent for production | Balance simplicity and flexibility |

---

## Updated Technical Context

All NEEDS CLARIFICATION items resolved:

- **Primary Dependencies**: UV for workspace management, import-linter for dependency validation
- **Testing**: pytest with test/unit/, test/integration/, test/e2e/ organization
- **Storage**: File system structure with build/ and dist/ separation
- **Versioning**: Single version (v0.x.x) for POC, independent component versions for production
- **Architecture Pattern**: Orchestrator pattern with interface-based component registry

---

## Next Steps

Proceed to Phase 1:
1. Generate data-model.md (structure metadata)
2. Create contracts/structure_schema.json (validation schema)
3. Create quickstart.md (developer onboarding guide)
4. Update agent context files

All research complete. Ready for design phase.
