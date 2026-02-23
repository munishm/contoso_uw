# Tasks: Basic Project Structure

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)  
**Generated**: 15 December 2025  
**Status**: Ready for Implementation

**Input**: Design documents from `/specs/001-project-structure/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: No tests requested in specification - implementation tasks only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Initialize the repository with foundational structure and tooling

- [ ] T001 Create top-level directories: src/, test/, docs/, specs/, build/, dist/
- [ ] T002 [P] Initialize UV workspace with root pyproject.toml at repository root
- [ ] T003 [P] Create comprehensive .gitignore file at repository root with Python, environment, build, and IDE patterns
- [ ] T004 [P] Create .env.example template file at repository root with placeholder variables

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create src/interfaces/ directory for component contracts
- [ ] T006 [P] Create src/shared/ directory with subdirectories: utils/, models/, schemas/, config/
- [ ] T007 [P] Create test/ subdirectories: unit/, integration/, e2e/, test_utils/
- [ ] T008 [P] Create test/conftest.py for shared pytest fixtures
- [ ] T009 [P] Create docs/ subdirectories: architecture/, adr/, guides/, api/
- [ ] T010 Setup import-linter configuration at repository root (.import-linter.ini) with layering rules
- [ ] T011 [P] Create contracts/structure_schema.json validation schema (already exists from planning)
- [ ] T012 [P] Create root README.md explaining monorepo structure per FR-009

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Organized File Organization (Priority: P1) 🎯 MVP

**Goal**: Establish consistent, well-organized monorepo directory structure with snake_case naming and clear component organization

**Independent Test**: Can be fully tested by examining directory structure, verifying all standard directories exist with clear purposes, and having developers successfully navigate to expected file locations within 30 seconds

### Implementation for User Story 1

- [ ] T013 [P] [US1] Create src/document_classification/ component directory with __init__.py
- [ ] T014 [P] [US1] Create src/entity_extraction/ component directory with __init__.py
- [ ] T015 [P] [US1] Create src/document_summarization/ component directory with __init__.py
- [ ] T016 [P] [US1] Create src/orchestration/ directory for workflow orchestration with __init__.py
- [ ] T017 [US1] Create README.md files in each component directory explaining purpose and structure
- [ ] T018 [P] [US1] Create test/unit/document_classification/ directory mirroring source structure
- [ ] T019 [P] [US1] Create test/unit/entity_extraction/ directory mirroring source structure
- [ ] T020 [P] [US1] Create test/unit/document_summarization/ directory mirroring source structure
- [ ] T021 [P] [US1] Create test/unit/shared/ directory for shared utility tests
- [ ] T022 [US1] Create docs/architecture/component_overview.md documenting all components
- [ ] T023 [P] [US1] Create docs/architecture/diagrams/ subdirectory for architecture diagrams
- [ ] T024 [US1] Validate all directory names follow snake_case convention (automated check)

**Checkpoint**: At this point, User Story 1 should be fully functional - developers can navigate the structure intuitively and locate components within 30 seconds

---

## Phase 4: User Story 2 - Component Reusability (Priority: P2)

**Goal**: Enable self-contained components with their own dependencies while sharing common utilities across the monorepo

**Independent Test**: Can be tested by creating a shared utility or component, placing it in the designated directory, and successfully importing/referencing it from multiple different components without duplication

### Implementation for User Story 2

- [ ] T025 [P] [US2] Create pyproject.toml in src/document_classification/ with UV project configuration
- [ ] T026 [P] [US2] Create pyproject.toml in src/entity_extraction/ with UV project configuration
- [ ] T027 [P] [US2] Create pyproject.toml in src/document_summarization/ with UV project configuration
- [ ] T028 [P] [US2] Create src/shared/utils/file_helpers.py with common file utilities
- [ ] T029 [P] [US2] Create src/shared/utils/validation.py with data validation utilities
- [ ] T030 [P] [US2] Create src/shared/models/document.py with shared Document model
- [ ] T031 [P] [US2] Create src/shared/models/entity.py with shared Entity model
- [ ] T032 [US2] Create src/shared/schemas/document_schema.json with JSON schema for documents
- [ ] T033 [US2] Update UV root pyproject.toml to reference all component workspaces
- [ ] T034 [US2] Create docs/guides/shared_utilities.md documenting shared resources
- [ ] T035 [US2] Validate components can import from src/shared/ without circular dependencies

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - components can use shared utilities without duplication

---

## Phase 5: User Story 3 - Clear Separation of Concerns (Priority: P2)

**Goal**: Clearly separate different types of code and resources (source code, tests, documentation, configuration, build artifacts)

**Independent Test**: Can be tested by verifying that source code, test files, documentation, and configurations reside in distinctly separate directories, and that build processes respect these boundaries

### Implementation for User Story 3

- [ ] T036 [P] [US3] Create .gitkeep files in build/ and dist/ directories to preserve structure
- [ ] T037 [P] [US3] Update .gitignore to exclude build/ and dist/ contents but preserve directories
- [ ] T038 [P] [US3] Create test/integration/test_orchestration.py placeholder for integration tests
- [ ] T039 [P] [US3] Create test/e2e/test_document_processing_workflow.py placeholder for E2E tests
- [ ] T040 [P] [US3] Create test/e2e/fixtures/ directory for test fixtures
- [ ] T041 [P] [US3] Create test/test_utils/mocks/ directory for mock utilities
- [ ] T042 [P] [US3] Create test/test_utils/helpers.py with test helper functions
- [ ] T043 [US3] Create docs/guides/testing_strategy.md documenting test organization
- [ ] T044 [US3] Validate test files are completely separated from source code
- [ ] T045 [US3] Validate build outputs can be cleaned without affecting source

**Checkpoint**: All user stories 1-3 should now be independently functional - clear separation enables different teams to work on code, tests, and docs without interference

---

## Phase 6: User Story 4 - Environment Configuration Management (Priority: P3)

**Goal**: Support environment-specific configurations without hardcoding values in the codebase

**Independent Test**: Can be tested by creating environment-specific configuration files, placing them in the designated directory, and verifying that different components can access environment-specific settings without modifying source code

### Implementation for User Story 4

- [ ] T046 [P] [US4] Create .env.dev file with development environment variables (gitignored)
- [ ] T047 [P] [US4] Create .env.staging file with staging environment variables (gitignored)
- [ ] T048 [P] [US4] Create .env.prod file with production environment variables (gitignored)
- [ ] T049 [US4] Update .env.example with comprehensive template for all environment variables
- [ ] T050 [P] [US4] Create src/shared/config/env_loader.py for loading environment configurations
- [ ] T051 [P] [US4] Create src/shared/config/__init__.py with config module exports
- [ ] T052 [US4] Update .gitignore to ensure all .env.* files (except .env.example) are excluded
- [ ] T053 [US4] Create docs/guides/environment_configuration.md documenting configuration management
- [ ] T054 [US4] Validate components can load environment-specific settings without hardcoding

**Checkpoint**: All four user stories should now be independently functional - environment configurations support multi-environment deployments

---

## Phase 7: Component Interfaces (Foundation for Pluggability)

**Purpose**: Define interfaces that enable plug-and-play component architecture (supports FR-015)

- [ ] T055 [P] Create src/interfaces/__init__.py with interface module exports
- [ ] T056 [P] Create src/interfaces/processor.py defining IDocumentProcessor Protocol
- [ ] T057 [P] Create src/interfaces/classifier.py defining IClassifier Protocol
- [ ] T058 [P] Create src/interfaces/extractor.py defining IEntityExtractor Protocol
- [ ] T059 [P] Create src/interfaces/summarizer.py defining ISummarizer Protocol
- [ ] T060 [P] Create src/interfaces/schemas/processor_schema.json for processor contract
- [ ] T061 Create docs/architecture/interface_contracts.md documenting all interfaces
- [ ] T062 Validate interfaces follow Protocol pattern and are importable from all components

---

## Phase 8: Orchestration Infrastructure (Component Communication)

**Purpose**: Implement orchestrator pattern for component coordination (from research.md decision)

- [ ] T063 [P] Create src/orchestration/__init__.py with orchestration module exports
- [ ] T064 Create src/orchestration/workflow.py defining WorkflowOrchestrator class
- [ ] T065 [P] Create src/orchestration/registry.py implementing component registry
- [ ] T066 [P] Create src/orchestration/pipeline.py defining pipeline builder
- [ ] T067 Create docs/architecture/orchestration_pattern.md documenting orchestrator design
- [ ] T068 Validate components can be registered and orchestrated without direct coupling

---

## Phase 9: Validation & Quality Tooling

**Purpose**: Automated validation of structure compliance and quality enforcement

- [ ] T069 [P] Create scripts/validate_structure.py to validate directory structure against schema
- [ ] T070 [P] Create scripts/check_naming.py to validate snake_case naming convention
- [ ] T071 [P] Create scripts/check_imports.py wrapper for import-linter validation
- [ ] T072 Create .pre-commit-config.yaml with structure validation hooks
- [ ] T073 [P] Create scripts/generate_structure_docs.py to auto-generate structure documentation
- [ ] T074 [P] Update UV root pyproject.toml with development dependencies (pytest, mypy, import-linter)
- [ ] T075 Create docs/guides/development_workflow.md documenting validation tools
- [ ] T076 Validate all scripts are executable and pass quality checks

---

## Phase 10: Documentation & Onboarding

**Purpose**: Complete documentation for developer onboarding and structure understanding

- [ ] T077 [P] Create docs/README.md with documentation overview
- [ ] T078 [P] Create docs/architecture/adr/001-monorepo-structure.md documenting architecture decision
- [ ] T079 [P] Create docs/architecture/adr/002-component-interfaces.md documenting interface strategy
- [ ] T080 [P] Create docs/architecture/adr/003-orchestrator-pattern.md documenting orchestration choice
- [ ] T081 [P] Create docs/guides/adding_new_component.md with component creation guide
- [ ] T082 [P] Create docs/guides/component_dependencies.md explaining dependency management
- [ ] T083 [P] Update root README.md with quick start guide and directory explanation per FR-009
- [ ] T084 [P] Copy specs/001-project-structure/quickstart.md to docs/guides/quickstart.md
- [ ] T085 Create .github/workflows/structure-validation.yml for CI validation
- [ ] T086 Validate quickstart guide can be completed in under 30 minutes (SC-006)

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Final refinements and quality improvements

- [ ] T087 [P] Review all README.md files for clarity and completeness
- [ ] T088 [P] Review all .gitignore patterns for security and completeness
- [ ] T089 [P] Validate all pyproject.toml files have consistent formatting
- [ ] T090 Run structure validation scripts and fix any issues
- [ ] T091 Run import-linter and resolve any layering violations
- [ ] T092 [P] Create CONTRIBUTING.md with contribution guidelines
- [ ] T093 [P] Create CHANGELOG.md for tracking structural changes
- [ ] T094 Survey team members on directory purpose understanding (SC-005)
- [ ] T095 Time new developer onboarding and validate under 30 minutes (SC-006)
- [ ] T096 Run full quickstart.md validation with fresh developer

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1 - MVP): Can start after Foundational
  - User Story 2 (P2): Can start after Foundational (integrates with US1 structure)
  - User Story 3 (P2): Can start after Foundational (uses US1 structure)
  - User Story 4 (P3): Can start after Foundational (integrates with US2 for config utilities)
- **Component Interfaces (Phase 7)**: Can start after Foundational (parallel with user stories)
- **Orchestration (Phase 8)**: Depends on Component Interfaces (Phase 7)
- **Validation (Phase 9)**: Can start after User Stories 1-4 complete
- **Documentation (Phase 10)**: Can start after Phases 7-8 complete
- **Polish (Phase 11)**: Depends on all previous phases

### User Story Dependencies

- **User Story 1 (P1 - MVP)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Uses US1 directory structure
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Uses US1 directory structure
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Integrates with US2 shared config utilities

### Within Each User Story

- Directory creation tasks marked [P] can run in parallel
- File creation tasks marked [P] can run in parallel within same phase
- Documentation tasks can run in parallel with implementation
- Validation tasks must run after implementation tasks complete

### Parallel Opportunities

**Phase 1 (Setup)**: T001, T002, T003, T004 can all run in parallel (different files)

**Phase 2 (Foundational)**: T006, T007, T008, T009, T011, T012 can run in parallel

**Phase 3 (User Story 1)**:
- T013, T014, T015, T016 (component directories) in parallel
- T018, T019, T020, T021 (test directories) in parallel
- T022, T023 (documentation) in parallel

**Phase 4 (User Story 2)**:
- T025, T026, T027 (pyproject.toml files) in parallel
- T028, T029, T030, T031, T032 (shared utilities) in parallel

**Phase 5 (User Story 3)**:
- T036, T037, T038, T039, T040, T041, T042 all in parallel

**Phase 6 (User Story 4)**:
- T046, T047, T048, T050, T051 all in parallel

**Phase 7 (Interfaces)**: T055-T060 all in parallel

**Phase 8 (Orchestration)**: T063, T065, T066 in parallel (T064 depends on registry)

**Phase 9 (Validation)**: T069, T070, T071, T073, T074 all in parallel

**Phase 10 (Documentation)**: T077-T084 all in parallel

**Phase 11 (Polish)**: T087, T088, T089, T092, T093 all in parallel

---

## Parallel Example: User Story 1

```bash
# All directory creation tasks can run simultaneously:
mkdir -p src/document_classification src/entity_extraction src/document_summarization src/orchestration &
mkdir -p test/unit/document_classification test/unit/entity_extraction test/unit/document_summarization &
mkdir -p docs/architecture/diagrams &

# After directories exist, create files in parallel:
touch src/document_classification/__init__.py &
touch src/entity_extraction/__init__.py &
touch src/document_summarization/__init__.py &
touch src/orchestration/__init__.py &

# Wait for all parallel tasks to complete
wait

# Then proceed with dependent tasks
echo "User Story 1 directories created" >> docs/architecture/component_overview.md
```

---

## Parallel Example: User Story 2

```bash
# All pyproject.toml files can be created in parallel:
cat > src/document_classification/pyproject.toml << EOF &
[project]
name = "contoso-document-classification"
version = "0.1.0"
EOF

cat > src/entity_extraction/pyproject.toml << EOF &
[project]
name = "contoso-entity-extraction"
version = "0.1.0"
EOF

cat > src/document_summarization/pyproject.toml << EOF &
[project]
name = "contoso-document-summarization"
version = "0.1.0"
EOF

# All shared utilities can be created in parallel:
touch src/shared/utils/file_helpers.py &
touch src/shared/utils/validation.py &
touch src/shared/models/document.py &
touch src/shared/models/entity.py &

# Wait for all tasks
wait

echo "User Story 2 component dependencies configured"
```

---

## Implementation Strategy

### MVP Scope (Recommended First Iteration)

Focus on delivering User Story 1 only for initial MVP:
- Phase 1: Setup
- Phase 2: Foundational
- Phase 3: User Story 1 (Organized File Organization)
- Phase 9: Basic validation
- Phase 11: Essential documentation

**Why**: This delivers immediate value (SC-001, SC-002) and enables developers to start working productively within the structure. Other user stories can be added incrementally.

### Incremental Delivery Plan

1. **Sprint 1 (MVP)**: Phases 1-3 + T069-T070 + T083
   - Deliverable: Working directory structure developers can navigate
   - Success: New developer locates entry point in <1 minute (SC-001)

2. **Sprint 2**: Phase 4 (US2) + Phase 7 (Interfaces)
   - Deliverable: Components with dependencies + interface contracts
   - Success: Shared utilities prevent duplication (SC-003)

3. **Sprint 3**: Phase 5 (US3) + Phase 6 (US4) + Phase 8 (Orchestration)
   - Deliverable: Complete separation of concerns + environment configs
   - Success: Tests separated, build processes automated (SC-004)

4. **Sprint 4**: Phase 9 (Validation) + Phase 10 (Documentation) + Phase 11 (Polish)
   - Deliverable: Full automation + comprehensive docs
   - Success: Onboarding under 30 minutes (SC-006)

### Quality Gates

- **After Phase 2**: Run T069 (structure validation) - must pass
- **After Phase 3**: Survey developers (SC-002) - 90% correct placement
- **After Phase 7**: Run T071 (import-linter) - no violations
- **After Phase 10**: Run T086 (quickstart validation) - under 30 minutes
- **After Phase 11**: Run T094-T096 (final validation) - all success criteria met

---

## Success Criteria Validation

**How tasks map to success criteria from spec.md:**

- **SC-001** (Locate entry point <1 minute): Validated by T086, T095
- **SC-002** (90% correct component placement): Validated by T094 survey
- **SC-003** (Zero duplicate utility code): Validated by T035, code review
- **SC-004** (Build process automation): Validated by T045, T085
- **SC-005** (Team agrees on directory purpose): Validated by T094 survey
- **SC-006** (Onboarding <30 minutes): Validated by T086, T095, T096

---

## Task Statistics

- **Total Tasks**: 96
- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 8 tasks
- **Phase 3 (User Story 1 - P1)**: 12 tasks
- **Phase 4 (User Story 2 - P2)**: 11 tasks
- **Phase 5 (User Story 3 - P2)**: 10 tasks
- **Phase 6 (User Story 4 - P3)**: 9 tasks
- **Phase 7 (Interfaces)**: 8 tasks
- **Phase 8 (Orchestration)**: 6 tasks
- **Phase 9 (Validation)**: 8 tasks
- **Phase 10 (Documentation)**: 10 tasks
- **Phase 11 (Polish)**: 10 tasks

**Parallelizable Tasks**: 63 tasks marked [P] can run in parallel within their phases

**MVP Minimum**: 24 tasks (Phases 1-3 + essential validation)

**Estimated Timeline**:
- MVP (Sprint 1): 2-3 days (24 tasks, many parallelizable)
- Full Implementation (Sprints 1-4): 2-3 weeks (96 tasks)

---

## Notes

- **No tests included**: Specification did not request TDD approach
- **Validation focus**: Emphasis on automated structure validation (import-linter, schema validation)
- **Documentation priority**: High focus on onboarding and ADRs for maintainability
- **Incremental delivery**: MVP-first approach enables fast feedback
- **Parallel execution**: 65% of tasks can run in parallel with proper tooling

---

**Next Steps**: Execute tasks starting with Phase 1 (Setup), proceed through Foundational phase, then begin User Story 1 for MVP delivery.
