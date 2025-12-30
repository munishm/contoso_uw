# Tasks: Schema-Based Document Extraction

**Input**: Design documents from `/specs/005-document-extraction-schema/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: Not explicitly requested in specification - implementation-focused tasks only

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Uses existing FastAPI backend structure: `src/api/`, `tests/api/`, `tests/integration/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Azure service setup

- [ ] T001 Provision Azure Cosmos DB database with containers: extraction_schemas, extraction_models, extraction_results
- [ ] T002 Configure Azure AI Document Intelligence endpoint and credentials in Azure Key Vault
- [ ] T003 [P] Configure Azure OpenAI Service endpoint and deployment (GPT-4) in Azure Key Vault
- [ ] T004 [P] Add dependencies to src/api/pyproject.toml: azure-cosmos, azure-ai-formrecognizer, azure-ai-openai, jsonschema

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, repositories, and service base classes that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create Citation value object in src/api/models/citation.py with BoundingBox and page/bbox types
- [ ] T006 [P] Create enums in src/api/models/enums.py: ModelType, CitationLevel, ExtractionStatus, CombinationStrategy, ConflictResolution
- [ ] T007 Create DocumentType model in src/api/models/schema.py with id, name, description, is_active fields
- [ ] T008 Create DocumentTypeVersion model in src/api/models/schema.py with version, input_schema, output_schema, model_config
- [ ] T009 [P] Create ExtractionModel model in src/api/models/schema.py with name, type, endpoint, version, capabilities
- [ ] T010 Create SchemaRepository in src/api/repositories/schema_repository.py for Cosmos DB operations on extraction_schemas container
- [ ] T011 [P] Create ExtractionModelRepository in src/api/repositories/extraction_model_repository.py for Cosmos DB operations on extraction_models container
- [ ] T012 Create base ExtractionModelAdapter interface in src/api/services/model_adapters/base.py with extract(), get_confidence(), supports_document_type()
- [ ] T013 [P] Create SchemaService in src/api/services/schema_service.py with get_schema(), validate_schema(), list_versions()
- [ ] T014 Add Azure Cosmos DB client initialization in src/api/dependencies.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract Data from Typed Documents (Priority: P1) 🎯 MVP

**Goal**: Enable extraction of structured data from a single document type using a defined schema, returning all fields with proper values or null indicators

**Independent Test**: Submit a Bank Statement v2.0 document, verify all required fields are extracted correctly with proper values

### Implementation for User Story 1

- [ ] T015 [P] [US1] Create ExtractionResult model in src/api/models/extraction.py with document_id, version_id, status, models_used, processing_duration_ms
- [ ] T016 [P] [US1] Create ExtractedField model in src/api/models/extraction.py with field_name, value, value_type, confidence, citations, needs_review
- [ ] T017 [US1] Create ExtractionRepository in src/api/repositories/extraction_repository.py for Cosmos DB operations on extraction_results container
- [ ] T018 [US1] Implement AzureDocIntelligenceAdapter in src/api/services/model_adapters/azure_doc_intelligence.py to call Azure AI Document Intelligence prebuilt-document API
- [ ] T019 [US1] Implement result parsing in AzureDocIntelligenceAdapter to extract text, bounding boxes, and convert to normalized coordinates (0.0-1.0)
- [ ] T020 [US1] Implement ExtractionService.extract_document() in src/api/services/extraction_service.py to orchestrate schema lookup, model execution, and result storage
- [ ] T021 [US1] Implement schema field mapping in ExtractionService to match extracted data to output_schema fields
- [ ] T022 [US1] Implement null value handling for missing required fields with clear indicators in ExtractionService
- [ ] T023 [US1] Add output schema validation in ExtractionService using jsonschema library to validate against output_schema rules
- [ ] T024 [US1] Create POST /api/v1/documents/{document_id}/extract endpoint in src/api/routes/extraction_routes.py
- [ ] T025 [US1] Create GET /api/v1/extractions/{extraction_id} endpoint in src/api/routes/extraction_routes.py
- [ ] T026 [US1] Add extraction status tracking and logging to ExtractionService with document_type, version, duration, success/failure

**Checkpoint**: At this point, User Story 1 should be fully functional - can extract from one document type with one model

---

## Phase 4: User Story 2 - Configure Multiple Extraction Models (Priority: P2)

**Goal**: Enable configuration of multiple models (OCR, layout, LLM) with combination strategies for each document type

**Independent Test**: Configure OCR+Layout for a document type, verify both models execute and results are combined according to strategy

### Implementation for User Story 2

- [ ] T027 [P] [US2] Implement AzureOpenAIAdapter in src/api/services/model_adapters/azure_openai.py with structured extraction using JSON mode
- [ ] T028 [P] [US2] Add few-shot prompting template builder in AzureOpenAIAdapter for accurate field extraction
- [ ] T029 [US2] Implement ModelPipelineExecutor in src/api/services/extraction_service.py to execute models in configured order
- [ ] T030 [US2] Implement sequential combination strategy in ModelPipelineExecutor (Model B processes Model A output)
- [ ] T031 [P] [US2] Implement parallel combination strategy in ModelPipelineExecutor (models run concurrently, results merged)
- [ ] T032 [US2] Implement fallback chain logic in ModelPipelineExecutor to invoke next model when confidence < threshold
- [ ] T033 [US2] Add confidence threshold checking per document type version from model_config
- [ ] T034 [US2] Create POST /api/v1/extraction-models endpoint in src/api/routes/schema_routes.py for model registration
- [ ] T035 [US2] Create GET /api/v1/extraction-models endpoint in src/api/routes/schema_routes.py to list available models
- [ ] T036 [US2] Add model configuration validation in SchemaService to ensure referenced model IDs exist

**Checkpoint**: At this point, User Story 2 should be functional - can configure and use multiple models per document type

---

## Phase 5: User Story 3 - Track Extraction Citations (Priority: P2)

**Goal**: Include page-level or bounding-box citations for every extracted field value

**Independent Test**: Extract from multi-page document, verify each field includes citation metadata with correct page numbers or coordinates

### Implementation for User Story 3

- [ ] T037 [P] [US3] Enhance AzureDocIntelligenceAdapter to capture bounding box coordinates from AnalyzeResult
- [ ] T038 [P] [US3] Implement coordinate normalization in AzureDocIntelligenceAdapter to convert pixel coordinates to 0.0-1.0 range based on page dimensions
- [ ] T039 [US3] Add citation collection logic in ExtractionService to aggregate citations per field from model outputs
- [ ] T040 [US3] Implement page-level citation generation when citation_level = "page" in schema version
- [ ] T041 [US3] Implement bounding-box citation generation when citation_level = "bounding_box" in schema version
- [ ] T042 [US3] Handle multiple citation locations for fields extracted from multiple document locations (e.g., repeated headers)
- [ ] T043 [US3] Add text_snippet extraction to citations for context (max 500 chars) in ExtractionService
- [ ] T044 [US3] Ensure 100% citation coverage validation - all successfully extracted fields must have at least one citation

**Checkpoint**: At this point, User Story 3 should be functional - all extractions include proper citations

---

## Phase 6: User Story 4 - Version Document Schemas (Priority: P3)

**Goal**: Support multiple versions of the same document type with different schemas and extraction configurations

**Independent Test**: Submit two documents of same type but different versions (v1.0 vs v2.0), verify each uses correct schema

### Implementation for User Story 4

- [ ] T045 [P] [US4] Create POST /api/v1/document-types endpoint in src/api/routes/schema_routes.py for document type registration
- [ ] T046 [P] [US4] Create POST /api/v1/document-types/{document_type_id}/versions endpoint in src/api/routes/schema_routes.py for version creation
- [ ] T047 [US4] Implement schema version lookup by document_type_id and version in SchemaService
- [ ] T048 [US4] Add version compatibility validation in SchemaService when updating schemas to detect breaking changes
- [ ] T049 [US4] Implement schema migration helper in SchemaService to map old field names to new field names for backward compatibility
- [ ] T050 [US4] Add version metadata to ExtractionResult to track which schema version was used
- [ ] T051 [US4] Create GET /api/v1/document-types endpoint in src/api/routes/schema_routes.py to list all document types
- [ ] T052 [US4] Create GET /api/v1/document-types/{document_type_id}/versions endpoint in src/api/routes/schema_routes.py to list versions
- [ ] T053 [US4] Implement runtime schema updates without application restart using Cosmos DB change feed notifications

**Checkpoint**: At this point, User Story 4 should be functional - can manage multiple schema versions

---

## Phase 7: Cross-Cutting Concerns & Polish

**Purpose**: Error handling, human review workflows, and production readiness

- [ ] T054 [P] Implement unknown document type rejection with error response requiring manual type specification in ExtractionService
- [ ] T055 [P] Implement poor scan quality handling - return extraction attempt with low confidence flags and review indicators
- [ ] T056 Implement ensemble conflict resolution in ModelPipelineExecutor - when models produce conflicting values with similar confidence, return all values and flag for review
- [ ] T057 [P] Create POST /api/v1/extractions/{extraction_id}/fields/{field_name}/review endpoint in src/api/routes/extraction_routes.py for human review submission
- [ ] T058 Implement FieldReviewRequest model and review action handling (confirm, correct, reject) in src/api/models/extraction.py
- [ ] T059 [P] Add schema configuration error validation - detect references to non-existent models and return validation errors
- [ ] T060 [P] Implement extraction performance metrics logging to Azure Application Insights: duration, model performance, confidence distribution
- [ ] T061 Implement caching for schema registry with 5-minute TTL to meet <100ms lookup requirement
- [ ] T062 [P] Add extraction result pagination for GET /api/v1/documents/{document_id}/extractions endpoint
- [ ] T063 Create POST /api/v1/document-types/{document_type_id}/versions/{version}/validate endpoint in src/api/routes/schema_routes.py for schema validation
- [ ] T064 [P] Add comprehensive error responses with proper HTTP status codes and error messages for all endpoints
- [ ] T065 Update API documentation with extraction workflow examples and integrate OpenAPI spec from contracts/extraction-api.yaml

---

## Dependencies Summary

### Phase Dependencies
- **Phase 1 → Phase 2**: Azure services must be provisioned before foundation code
- **Phase 2 → Phases 3-6**: Foundation (models, repos, base adapters) blocks all user stories
- **Phases 3, 4, 5, 6**: User stories can be implemented in parallel after Phase 2 completes
- **Phase 7**: Depends on Phases 3-6 for cross-cutting integration

### User Story Dependencies
- **US1 (P1)**: No dependencies - implements core extraction
- **US2 (P2)**: Depends on US1 (T015-T026) for base extraction service
- **US3 (P2)**: Depends on US1 (T018-T019) for model adapter integration
- **US4 (P3)**: Depends on US1 (T020) for schema service integration

### Critical Path
```
T001-T004 (Setup) → T005-T014 (Foundation) → T015-T026 (US1 Core) → T027-T036 (US2 Multi-model) → T054-T065 (Polish)
```

### Parallel Opportunities

**After Phase 2 completes, these can run in parallel:**
- US1 Implementation (T015-T026)
- US3 Citation setup (T037-T038) - can prepare adapters
- US4 Schema routes (T045-T046) - independent of extraction logic

**Within Phase 7, these are independent:**
- Error handling (T054-T056, T059)
- Review workflow (T057-T058)
- Metrics & monitoring (T060-T061)
- Documentation (T064-T065)

---

## Delivery Strategy

### MVP (Minimum Viable Product)
**Scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1 only)
**Outcome**: Extract structured data from one document type using one model with citations
**Validation**: Meets SC-002 (90%+ extraction accuracy), SC-003 (citations for all fields)

### Increment 2
**Add**: Phase 4 (User Story 2)
**Outcome**: Support multiple models with fallback chains
**Validation**: Meets SC-006 (95%+ availability with fallback)

### Increment 3
**Add**: Phase 5 (User Story 3) + Phase 6 (User Story 4)
**Outcome**: Full citation tracking and schema versioning
**Validation**: Meets SC-004 (concurrent version processing), SC-005 (2 min verification)

### Production Release
**Add**: Phase 7 (Polish)
**Outcome**: Production-ready with error handling, review workflows, and monitoring
**Validation**: Meets all success criteria SC-001 through SC-008

---

## Task Count Summary

| Phase | Task Count | Parallelizable |
|-------|-----------|----------------|
| Phase 1: Setup | 4 | 2 |
| Phase 2: Foundational | 10 | 5 |
| Phase 3: US1 (P1) | 12 | 2 |
| Phase 4: US2 (P2) | 10 | 3 |
| Phase 5: US3 (P2) | 8 | 2 |
| Phase 6: US4 (P3) | 9 | 2 |
| Phase 7: Polish | 12 | 7 |
| **Total** | **65** | **23** |

**Estimated Effort**: 
- Setup & Foundation: 1-2 weeks
- User Story 1 (MVP): 2-3 weeks
- User Stories 2-4: 3-4 weeks
- Polish & Production: 1-2 weeks
- **Total**: 7-11 weeks (fits within 8-12 week POC timeline from Constitution)

---

## Validation Checklist

Before marking each phase complete, verify:

- [ ] **Phase 1**: All Azure services provisioned and accessible
- [ ] **Phase 2**: All models, repositories, and base services created with unit tests passing
- [ ] **Phase 3**: Can extract from one document type end-to-end with citations
- [ ] **Phase 4**: Can configure multiple models with fallback working
- [ ] **Phase 5**: All extracted fields include proper citations
- [ ] **Phase 6**: Multiple schema versions coexist without conflicts
- [ ] **Phase 7**: Error handling, review workflow, and monitoring operational

---

## Notes

- **Test Strategy**: Tests not explicitly requested in spec, so implementation-focused. Add contract/integration tests if needed during development.
- **Parallel Execution**: 23 tasks marked [P] can run in parallel within their phases, reducing calendar time.
- **File Paths**: All tasks include concrete file paths in `src/api/` following existing FastAPI patterns.
- **Constitution Compliance**: Task organization follows Principle 8 (Reusable Patterns) and avoids framework wrapping (Principle: Anti-Framework Wrapping).
