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

Uses entity extraction module structure: `src/entity_extraction/`, integrated with `src/orchestration/` workflows

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Azure service setup

- [ ] T001 Provision Azure Cosmos DB database with containers: extraction_schemas, extraction_models, extraction_results
- [ ] T002 Configure Azure OpenAI Service endpoint and deployment (GPT-4 Vision) in Azure Key Vault for OCR and entity extraction
- [ ] T003 [P] Add dependencies to src/entity_extraction/pyproject.toml: azure-cosmos, azure-ai-openai, jsonschema, pydantic

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, repositories, and service base classes that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create Citation value object in src/entity_extraction/models/citation.py with BoundingBox and page/bbox types
- [ ] T006 [P] Create enums in src/entity_extraction/models/enums.py: ModelType, CitationLevel, ExtractionStatus, CombinationStrategy, ConflictResolution
- [ ] T007 Create DocumentType model in src/entity_extraction/models/schema.py with id, name, description, is_active fields
- [ ] T008 Create DocumentTypeVersion model in src/entity_extraction/models/schema.py with version, input_schema, output_schema, model_config
- [ ] T009 [P] Create ExtractionModel model in src/entity_extraction/models/schema.py with name, type, endpoint, version, capabilities
- [ ] T010 Create SchemaRepository in src/entity_extraction/repositories/schema_repository.py for Cosmos DB operations on extraction_schemas container
- [ ] T011 [P] Create ExtractionModelRepository in src/entity_extraction/repositories/extraction_model_repository.py for Cosmos DB operations on extraction_models container
- [ ] T012 Create base ExtractionModelAdapter interface in src/entity_extraction/adapters/base.py with extract(), get_confidence(), supports_document_type()
- [ ] T013 [P] Create SchemaService in src/entity_extraction/services/schema_service.py with get_schema(), validate_schema(), list_versions()
- [ ] T014 Add Azure Cosmos DB client initialization in src/entity_extraction/config.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract Data from Typed Documents (Priority: P1) 🎯 MVP

**Goal**: Enable extraction of structured data from a single document type using GPT-4 Vision for OCR and entity extraction

**Independent Test**: Submit a Bank Statement v2.0 document, verify all required fields are extracted correctly using GPT-4 Vision

### Implementation for User Story 1 (GPT-4 Vision Based)

- [ ] T015 [P] [US1] Create ExtractionResult model in src/entity_extraction/models/extraction.py with document_id, version_id, status, models_used, processing_duration_ms
- [ ] T016 [P] [US1] Create ExtractedField model in src/entity_extraction/models/extraction.py with field_name, value, value_type, confidence, citations, needs_review
- [ ] T017 [US1] Create ExtractionRepository in src/entity_extraction/repositories/extraction_repository.py for Cosmos DB operations on extraction_results container
- [ ] T018 [US1] Implement AzureOpenAIVisionAdapter in src/entity_extraction/adapters/azure_openai_vision.py to call GPT-4 Vision API for OCR and structured extraction
- [ ] T019 [US1] Implement prompt engineering in AzureOpenAIVisionAdapter with schema-aware prompts for accurate field extraction from document images
- [ ] T020 [US1] Implement bounding box estimation in AzureOpenAIVisionAdapter using GPT-4 Vision's spatial understanding capabilities
- [ ] T021 [US1] Implement SchemaExtractionService.extract_document() in src/entity_extraction/services/schema_extraction_service.py to orchestrate schema lookup, GPT-4 Vision execution, and result storage
- [ ] T022 [US1] Implement schema field mapping in SchemaExtractionService to match extracted data to output_schema fields
- [ ] T023 [US1] Implement null value handling for missing required fields with clear indicators in SchemaExtractionService
- [ ] T024 [US1] Add output schema validation in SchemaExtractionService using jsonschema library to validate against output_schema rules
- [ ] T025 [US1] Create orchestration integration function in src/entity_extraction/services/orchestration_interface.py for workflow calls
- [ ] T026 [US1] Add extraction status tracking and logging to SchemaExtractionService with document_type, version, duration, success/failure

**Checkpoint**: At this point, User Story 1 should be fully functional - can extract from one document type using GPT-4 Vision

---

## Phase 4: User Story 2 - Add Azure Document Intelligence (Priority: P2)

**Goal**: Add Azure Document Intelligence as an alternative/fallback model to GPT-4 Vision for document extraction

**Independent Test**: Configure Document Intelligence as fallback, verify it executes when GPT-4 Vision confidence is low

### Implementation for User Story 2 (Add Document Intelligence)

- [ ] T027 [US2] Configure Azure AI Document Intelligence endpoint and credentials in Azure Key Vault
- [ ] T028 [US2] Add azure-ai-formrecognizer dependency to src/entity_extraction/pyproject.toml
- [ ] T029 [US2] Implement AzureDocIntelligenceAdapter in src/entity_extraction/adapters/azure_doc_intelligence.py to call Azure AI Document Intelligence prebuilt-document API
- [ ] T030 [US2] Implement result parsing in AzureDocIntelligenceAdapter to extract text, bounding boxes, and convert to normalized coordinates (0.0-1.0)
- [ ] T031 [US2] Implement ModelPipelineExecutor in src/entity_extraction/services/schema_extraction_service.py to execute models in configured order
- [ ] T032 [US2] Implement sequential combination strategy in ModelPipelineExecutor (Model B processes Model A output)
- [ ] T033 [P] [US2] Implement parallel combination strategy in ModelPipelineExecutor (models run concurrently, results merged)
- [ ] T034 [US2] Implement fallback chain logic in ModelPipelineExecutor to invoke Document Intelligence when GPT-4 Vision confidence < threshold
- [ ] T035 [US2] Add confidence threshold checking per document type version from model_config
- [ ] T036 [US2] Add model configuration validation in SchemaService to ensure referenced model IDs exist

**Checkpoint**: At this point, User Story 2 should be functional - can use either GPT-4 Vision or Document Intelligence with fallback support

---

## Phase 5: User Story 3 - Track Extraction Citations (Priority: P2)

**Goal**: Include page-level or bounding-box citations for every extracted field value

**Independent Test**: Extract from multi-page document, verify each field includes citation metadata with correct page numbers or coordinates

### Implementation for User Story 3

- [ ] T037 [P] [US3] Enhance AzureOpenAIVisionAdapter to capture spatial information from GPT-4 Vision responses using visual grounding
- [ ] T038 [P] [US3] Enhance AzureDocIntelligenceAdapter to capture bounding box coordinates from AnalyzeResult
- [ ] T039 [US3] Implement coordinate normalization in both adapters to convert to 0.0-1.0 range based on page dimensions
- [ ] T040 [US3] Add citation collection logic in SchemaExtractionService to aggregate citations per field from model outputs
- [ ] T041 [US3] Implement page-level citation generation when citation_level = "page" in schema version
- [ ] T042 [US3] Implement bounding-box citation generation when citation_level = "bounding_box" in schema version
- [ ] T043 [US3] Handle multiple citation locations for fields extracted from multiple document locations (e.g., repeated headers)
- [ ] T044 [US3] Add text_snippet extraction to citations for context (max 500 chars) in SchemaExtractionService
- [ ] T045 [US3] Ensure 100% citation coverage validation - all successfully extracted fields must have at least one citation

**Checkpoint**: At this point, User Story 3 should be functional - all extractions include proper citations

---

## Phase 6: User Story 4 - Version Document Schemas (Priority: P3)

**Goal**: Support multiple versions of the same document type with different schemas and extraction configurations

**Independent Test**: Submit two documents of same type but different versions (v1.0 vs v2.0), verify each uses correct schema

### Implementation for User Story 4

- [ ] T046 [P] [US4] Add create_document_type() method in SchemaService for document type registration
- [ ] T047 [P] [US4] Add create_schema_version() method in SchemaService for version creation
- [ ] T048 [US4] Implement schema version lookup by document_type_id and version in SchemaService
- [ ] T049 [US4] Add version compatibility validation in SchemaService when updating schemas to detect breaking changes
- [ ] T050 [US4] Implement schema migration helper in SchemaService to map old field names to new field names for backward compatibility
- [ ] T051 [US4] Add version metadata to ExtractionResult to track which schema version was used
- [ ] T052 [US4] Add list_document_types() method in SchemaService to retrieve all document types
- [ ] T053 [US4] Add list_schema_versions() method in SchemaService to retrieve versions for a document type
- [ ] T054 [US4] Implement runtime schema updates without application restart using Cosmos DB change feed notifications

**Checkpoint**: At this point, User Story 4 should be functional - can manage multiple schema versions

---

## Phase 7: Cross-Cutting Concerns & Polish

**Purpose**: Error handling, human review workflows, and production readiness

- [ ] T055 [P] Implement unknown document type rejection with error response requiring manual type specification in SchemaExtractionService
- [ ] T056 [P] Implement poor scan quality handling - return extraction attempt with low confidence flags and review indicators
- [ ] T057 Implement ensemble conflict resolution in ModelPipelineExecutor - when models produce conflicting values with similar confidence, return all values and flag for review
- [ ] T058 [P] Add review_field() method in SchemaExtractionService for human review submission
- [ ] T059 Implement FieldReviewRequest model and review action handling (confirm, correct, reject) in src/entity_extraction/models/extraction.py
- [ ] T060 [P] Add schema configuration error validation - detect references to non-existent models and return validation errors
- [ ] T061 [P] Implement extraction performance metrics logging to Azure Application Insights: duration, model performance, confidence distribution
- [ ] T062 Implement caching for schema registry with 5-minute TTL to meet <100ms lookup requirement
- [ ] T063 [P] Add list_extractions() method with pagination support in SchemaExtractionService
- [ ] T064 Add validate_schema_version() method in SchemaService for schema validation
- [ ] T065 [P] Add comprehensive error handling with custom exceptions (DocumentTypeMismatchError, SchemaValidationError, etc.)
- [ ] T066 Update module documentation with usage examples and integration patterns for orchestration workflows

---

## Dependencies Summary

### Phase Dependencies
- **Phase 1 → Phase 2**: Azure services must be provisioned before foundation code
- **Phase 2 → Phases 3-6**: Foundation (models, repos, base adapters) blocks all user stories
- **Phases 3, 4, 5, 6**: User stories can be implemented in parallel after Phase 2 completes
- **Phase 7**: Depends on Phases 3-6 for cross-cutting integration

### User Story Dependencies
- **US1 (P1)**: No dependencies - implements core extraction with GPT-4 Vision
- **US2 (P2)**: Depends on US1 (T015-T026) for base extraction service, adds Document Intelligence
- **US3 (P2)**: Depends on US1 (T018-T020) and US2 (T029-T030) for model adapter integration
- **US4 (P3)**: Depends on US1 (T021) for schema service integration

### Critical Path
```
T001-T003 (Setup) → T005-T014 (Foundation) → T015-T026 (US1 GPT-4 Vision) → T027-T036 (US2 Add Doc Intelligence) → T055-T066 (Polish)
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
**Outcome**: Extract structured data from one document type using GPT-4 Vision for OCR and entity extraction
**Validation**: Meets SC-002 (90%+ extraction accuracy), SC-003 (citations for all fields)

### Increment 2
**Add**: Phase 4 (User Story 2)
**Outcome**: Add Azure Document Intelligence as alternative/fallback to GPT-4 Vision
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
| Phase 1: Setup | 3 | 1 |
| Phase 2: Foundational | 10 | 5 |
| Phase 3: US1 GPT-4 Vision (P1) | 12 | 2 |
| Phase 4: US2 Add Doc Intelligence (P2) | 10 | 1 |
| Phase 5: US3 Citations (P2) | 9 | 2 |
| Phase 6: US4 Versioning (P3) | 9 | 2 |
| Phase 7: Polish | 12 | 7 |
| **Total** | **65** | **20** |

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
- [ ] **Phase 3**: Can extract from one document type end-to-end using GPT-4 Vision
- [ ] **Phase 4**: Document Intelligence adapter working with fallback from GPT-4 Vision
- [ ] **Phase 5**: All extracted fields include proper citations
- [ ] **Phase 6**: Multiple schema versions coexist without conflicts
- [ ] **Phase 7**: Error handling, review workflow, and monitoring operational

---

## Notes

- **Implementation Priority**: GPT-4 Vision is implemented first (Phase 3) as the primary extraction model, with Azure Document Intelligence added later (Phase 4) as an alternative/fallback option.
- **Module Architecture**: This is a Python module integrated with orchestration workflows, not a REST API. Tasks reflect module-based structure in `src/entity_extraction/`.
- **Test Strategy**: Tests not explicitly requested in spec, so implementation-focused. Add contract/integration tests if needed during development.
- **Parallel Execution**: 20 tasks marked [P] can run in parallel within their phases, reducing calendar time.
- **File Paths**: All tasks include concrete file paths in `src/entity_extraction/` following module-based patterns.
- **Constitution Compliance**: Task organization follows Principle 8 (Reusable Patterns) and avoids framework wrapping (Principle: Anti-Framework Wrapping).
