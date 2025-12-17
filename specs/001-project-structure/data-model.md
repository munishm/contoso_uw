# Data Model: Basic Project Structure

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)  
**Created**: 15 December 2025  
**Status**: Complete

## Purpose

This document defines the data model and metadata for the monorepo directory structure. While the "data" here is the file system structure itself, we model it to enable validation, documentation generation, and automated tooling.

---

## Core Entities

### 1. Directory Node

Represents any directory in the monorepo structure.

**Attributes**:
- `path` (string, required): Relative path from repository root (e.g., "src/document_classification")
- `name` (string, required): Directory name (must be snake_case per FR-008)
- `type` (enum, required): One of [component, shared, test, docs, build, config, root]
- `purpose` (string, required): Human-readable description of directory purpose
- `parent_path` (string, nullable): Path to parent directory, null for root
- `is_gitignored` (boolean, required): Whether directory should be in .gitignore
- `requires_readme` (boolean): Whether directory should have README.md

**Relationships**:
- `children` (array of Directory Node): Subdirectories
- `files` (array of File Node): Files within directory

**Constraints**:
- Path must be unique within repository
- Name must match snake_case pattern: `^[a-z][a-z0-9_]*$`
- Type must be valid enum value
- If type = "component", must be under src/ directory
- If is_gitignored = true, must be listed in .gitignore

### 2. File Node

Represents a file in the structure.

**Attributes**:
- `path` (string, required): Relative path from repository root
- `name` (string, required): File name with extension
- `type` (enum, required): One of [source, test, config, docs, ignore, secret, build]
- `purpose` (string, required): Description of file's role
- `parent_path` (string, required): Containing directory path
- `is_required` (boolean): Whether file MUST exist per spec (e.g., README.md, .gitignore)
- `is_gitignored` (boolean): Whether file should be excluded from version control
- `template_available` (boolean): Whether template exists for this file

**Relationships**:
- `parent_directory` (Directory Node): Containing directory

**Constraints**:
- If type = "secret", is_gitignored MUST be true (except .env.example)
- If type = "config" and name matches ".env.*", is_gitignored MUST be true
- If is_required = true, must exist in repository
- If name = ".env.example", is_gitignored MUST be false

### 3. Component

Represents a pluggable component (specialized Directory Node).

**Attributes**:
- Inherits all Directory Node attributes
- `component_name` (string, required): Human-readable component name
- `version` (string, required): Semantic version (e.g., "0.1.0")
- `dependencies` (array of string): Component names this depends on
- `interface_version` (string, required): Interface version implemented (e.g., "IProcessorV1")
- `has_package_manifest` (boolean, required): Whether has pyproject.toml (managed by UV)
- `is_deployable` (boolean, required): Whether component can be deployed independently

**Relationships**:
- `implements` (Interface): Interface contract component adheres to
- `tests` (Test Suite): Associated tests in test/ directory

**Constraints**:
- Path must start with "src/"
- Must not be "src/shared" or "src/interfaces"
- has_package_manifest MUST be true per FR-013
- component_name must match directory name conventions

### 4. Interface

Represents a component interaction contract.

**Attributes**:
- `name` (string, required): Interface name (e.g., "IDocumentProcessor")
- `version` (string, required): Semantic version
- `file_path` (string, required): Path to interface definition (e.g., "src/interfaces/processor.py")
- `methods` (array of Method): Interface methods/functions
- `schema_path` (string, nullable): Path to JSON schema if applicable
- `stability` (enum): One of [experimental, stable, deprecated]

**Relationships**:
- `implementors` (array of Component): Components implementing this interface

**Constraints**:
- file_path must be under "src/interfaces/"
- version must follow semantic versioning
- If stability = "deprecated", must have deprecation_note

### 5. Method

Represents a method in an Interface.

**Attributes**:
- `name` (string, required): Method name
- `signature` (string, required): Full method signature
- `parameters` (array of Parameter): Method parameters
- `returns` (string, required): Return type description
- `purpose` (string, required): What the method does
- `is_required` (boolean): Whether implementors MUST implement (vs optional)

### 6. Test Suite

Represents organized tests for a component.

**Attributes**:
- `component_name` (string, required): Component being tested
- `unit_test_path` (string, nullable): Path to unit tests (e.g., "test/unit/component_name/")
- `integration_test_path` (string, nullable): Path to integration tests
- `e2e_test_path` (string, nullable): Path to E2E tests
- `test_count` (integer): Number of test files
- `coverage_target` (float): Target code coverage percentage

**Relationships**:
- `tests` (Component): The component being tested

**Constraints**:
- At least one of unit/integration/e2e path must be non-null
- Paths must mirror src/ structure for unit tests
- coverage_target should be >= 80% per engineering standards

---

## Environment Configuration Model

### Environment Config

**Attributes**:
- `name` (string, required): Environment name (dev, staging, prod)
- `file_path` (string, required): Path to .env file
- `is_committed` (boolean, required): Whether file is in git (false except .env.example)
- `variables` (array of EnvVariable): Environment variables defined

**Constraints**:
- file_path must match pattern ".env.{name}" or ".env.example"
- If name != "example", is_committed MUST be false
- Must exist in .gitignore (except .env.example)

### EnvVariable

**Attributes**:
- `key` (string, required): Variable name (UPPER_SNAKE_CASE)
- `value_type` (enum, required): One of [string, integer, boolean, url, secret]
- `is_required` (boolean): Whether variable MUST be set
- `default_value` (string, nullable): Default if not set
- `description` (string, required): What the variable controls

---

## Monorepo Metadata

### Workspace

Represents the entire monorepo.

**Attributes**:
- `name` (string, required): Repository name (e.g., "HSBC_IWPB_UW")
- `root_path` (string, required): Absolute path to repository root
- `architecture` (enum, required): "monorepo"
- `naming_convention` (enum, required): "snake_case"
- `primary_language` (string, required): "python"
- `workspace_tool` (string, required): Tooling used (e.g., "poetry")
- `version` (string, required): Monorepo version (e.g., "0.1.0")

**Relationships**:
- `components` (array of Component): All components in src/
- `shared_resources` (Directory Node): src/shared/
- `interfaces` (array of Interface): All defined interfaces
- `environment_configs` (array of Environment Config): All .env files

**Computed Fields**:
- `total_components` (integer): Count of components
- `total_test_files` (integer): Count of all test files
- `structure_compliance_score` (float): Percentage of requirements met

---

## Relationships Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Workspace                           │
│  - name, version, architecture, naming_convention           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                ┌───────┴────────┐
                │                │
        ┌───────▼─────┐   ┌──────▼──────┐
        │  Component   │   │  Interface  │
        │              │   │             │
        └──────┬───────┘   └──────┬──────┘
               │                  │
               │ implements       │
               └──────────────────┘
                        │
               ┌────────▼────────┐
               │   Test Suite    │
               │                 │
               └─────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      Directory Node                          │
│  - path, name, type, purpose                                 │
└───────┬──────────────────────────────────────────────────────┘
        │
        ├── children (Directory Node[])
        │
        └── files (File Node[])
```

---

## Validation Rules

### Structure Validation

1. **Naming Convention** (FR-008):
   - All directories MUST match `^[a-z][a-z0-9_]*$` (snake_case)
   - Exceptions: Hidden directories (.), special dirs (node_modules)

2. **Required Directories** (FR-001 through FR-007):
   - `src/` MUST exist
   - `test/` MUST exist
   - `docs/` MUST exist
   - `test/unit/` and `test/e2e/` MUST exist

3. **Component Structure** (FR-005, FR-013):
   - Each directory under `src/` (except shared, interfaces) is a Component
   - Each Component MUST have `pyproject.toml` or equivalent
   - Components MUST implement at least one Interface

4. **Test Organization** (FR-002, FR-016):
   - `test/unit/` structure MUST mirror `src/` component structure
   - Each Component MUST have corresponding tests

5. **Security** (FR-012):
   - All `.env.*` files (except `.env.example`) MUST be in .gitignore
   - `build/` and `dist/` MUST be in .gitignore
   - `__pycache__/`, `*.pyc` MUST be in .gitignore

6. **Separation of Concerns** (FR-014):
   - No source files directly in repository root
   - Build outputs MUST be in build/ or dist/
   - Tests MUST be in test/, not mixed with source

### Dependency Validation

1. **Layering Rules** (from research.md):
   - `src/interfaces/` MUST NOT import from other src/ directories
   - `src/shared/` MAY import from `src/interfaces/` only
   - Components MAY import from `src/shared/` and `src/interfaces/`
   - Components importing other components MUST use interfaces

2. **Circular Dependency Prevention**:
   - Run `import-linter` to validate no circular imports
   - Fail CI build if circular dependencies detected

---

## Metadata Schema

The structure metadata is formalized in JSON Schema format (see [contracts/structure_schema.json](contracts/structure_schema.json)) to enable:

- **Validation**: Automated checking of structure compliance
- **Documentation**: Auto-generate structure documentation
- **Tooling**: IDE plugins, linters, scaffolding tools
- **CI/CD**: Pre-commit hooks and CI validation

---

## Example: Component Instance

```json
{
  "path": "src/document_classification",
  "name": "document_classification",
  "type": "component",
  "purpose": "Classifies documents into predefined types using AI",
  "component_name": "Document Classification",
  "version": "0.1.0",
  "dependencies": [],
  "interface_version": "IClassifierV1",
  "has_package_manifest": true,
  "is_deployable": true,
  "implements": {
    "name": "IDocumentClassifier",
    "version": "1.0.0",
    "file_path": "src/interfaces/classifier.py"
  },
  "tests": {
    "component_name": "document_classification",
    "unit_test_path": "test/unit/document_classification/",
    "test_count": 5,
    "coverage_target": 85.0
  }
}
```

---

## Usage

This data model supports:

1. **Structure Validation Scripts**: Verify monorepo adheres to all requirements
2. **Documentation Generation**: Auto-generate structure overview from metadata
3. **Scaffolding Tools**: Create new components with correct structure
4. **CI/CD Gates**: Block merges if structure requirements violated
5. **Developer Tools**: IDE plugins to enforce conventions

See [quickstart.md](quickstart.md) for developer usage of structure tooling.
