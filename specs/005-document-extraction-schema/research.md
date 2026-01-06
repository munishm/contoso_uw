# Research: Schema-Based Document Extraction

**Feature**: [spec.md](spec.md)  
**Date**: 29 December 2025  
**Status**: Complete

## Technical Context Resolution

### 1. Document Schema Storage Strategy

**Decision**: Azure Cosmos DB with versioned schema records

**Rationale**:
- Constitution Principle 9 mandates Azure-native services
- Constitution FR-001 requires versioned registry with audit history
- Cosmos DB provides JSON schema storage, versioning via partition keys, and automatic change feed for audit trails
- Supports SC-007 requirement for runtime updates without restart

**Alternatives Considered**:
- Azure SQL Database: Rejected - schema flexibility limited for evolving extraction definitions
- Azure Blob Storage (JSON files): Rejected - no transactional consistency, limited query capability
- Embedded in application: Rejected - violates SC-007 runtime update requirement

### 2. Extraction Model Integration Pattern

**Decision**: Plugin-based model adapter architecture with factory pattern

**Rationale**:
- FR-005 requires support for multiple model types (OCR, layout, custom ML)
- Existing `classification_service.py` and `processing_service.py` provide patterns
- Factory pattern enables adding new models without code changes to orchestration
- Aligns with Constitution Principle 8 (Reusable Patterns & Extensibility)

**Adapter Interface**:
```
ExtractionModelAdapter
├── extract(document, schema) → ExtractionResult
├── get_confidence() → float
├── supports_document_type(doc_type) → bool
└── get_model_metadata() → ModelInfo
```

**Alternatives Considered**:
- Hard-coded model calls: Rejected - violates extensibility requirement
- External microservice per model: Rejected - over-engineering for POC scope

### 3. Citation Coordinate System

**Decision**: Normalized coordinates (0.0-1.0) with page reference

**Rationale**:
- Confirmed in clarification session (2025-12-29)
- Resolution-independent citations work across different scan qualities
- Industry standard (Azure Document Intelligence returns normalized coords)
- Aligns with existing entity model's `source_location` field pattern

**Schema Format**:
```json
{
  "page": 1,
  "x": 0.12,
  "y": 0.45,
  "width": 0.08,
  "height": 0.02
}
```

### 4. Model Fallback and Ensemble Strategy

**Decision**: Configurable per-document-type with default 70% threshold

**Rationale**:
- Confirmed in clarification session (2025-12-29)
- Threshold configurable per document type allows tuning for criticality
- FR-006 explicitly requires fallback chain support
- FR-007a requires flagging conflicting values for human review

**Configuration Schema**:
```json
{
  "confidence_threshold": 0.7,
  "fallback_chain": ["primary_model", "fallback_model"],
  "conflict_resolution": "flag_for_review"
}
```

### 5. Azure Services Selection

**Decision**: Azure-native stack per Constitution Principle 9

| Capability | Azure Service | Notes |
|------------|---------------|-------|
| OCR/Layout | Azure AI Document Intelligence | Provides text, tables, key-value pairs, bounding boxes |
| LLM Extraction | Azure OpenAI (GPT-4) | Structured extraction with prompts, JSON mode |
| Schema Storage | Azure Cosmos DB | Document store with versioning |
| Model Registry | Azure ML Model Registry | Track extraction model versions |
| Monitoring | Azure Application Insights | Extraction performance metrics |

**Rationale**:
- All services pre-approved in HSBC Azure subscription
- Aligns with existing project infrastructure (see `infrastructure/bicep/`)

### 6. Integration with Existing Codebase

**Decision**: Extend `src/entity_extraction/` module with schema-based extraction

**Integration Points**:
- `src/entity_extraction/`: Add schema-based extraction services and models
- `src/orchestration/`: Call extraction module from workflow nodes
- `src/interfaces/`: Define shared extraction type contracts

**Existing Patterns to Follow**:
- Pydantic models with `Field` descriptions and validation
- Repository pattern for data access
- Service layer for business logic
- Async/await for I/O operations

**Module Interface**:
```python
# Called from orchestration workflows
from src.entity_extraction.services import SchemaExtractionService

extraction_service = SchemaExtractionService(
    schema_repo=schema_repository,
    extraction_repo=extraction_repository
)

# Usage in orchestration
result = await extraction_service.extract_document(
    document_id="doc-123",
    document_type_id="type-456",
    version="2.0.0"
)
```

### 7. Performance Targets

**Decision**: Align with Constitution Principle 6 POC targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Schema lookup | <100ms | Hot path, cached |
| Single field extraction | <1s | Per-field, parallel |
| Full document extraction | <2 min | 10-page document |
| Throughput | 100 docs/hour | SC-008 requirement |

**Implementation Notes**:
- Schema registry cached with 5-minute TTL
- Parallel model execution where strategy permits
- Async extraction with progress callbacks

## Best Practices Applied

### Azure AI Document Intelligence Integration

1. **Pre-built vs Custom Models**: Use pre-built "prebuilt-document" for general extraction, custom models for specific document types
2. **Analyze Result Structure**: Parse `AnalyzeResult` to extract text, tables, key-value pairs with bounding boxes
3. **Confidence Handling**: Document Intelligence returns confidence per word; aggregate to field level

### JSON Schema for Extraction Configuration

1. **JSON Schema Draft 7**: Use for input/output schema validation
2. **Schema Versioning**: Semantic versioning (type_name/version)
3. **Required vs Optional Fields**: Mark criticality in schema for human review triggers

### LLM-Based Extraction

1. **Structured Output**: Use Azure OpenAI JSON mode for reliable schema-conformant output
2. **Few-shot Prompting**: Include 2-3 examples per field type for accuracy
3. **Citation Injection**: Prompt LLM to include source text with response

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Model accuracy <90% | Medium | High | Multi-model ensemble, human review fallback |
| Schema evolution breaks extraction | Low | Medium | Version compatibility validation, migration scripts |
| Citation coordinates misaligned | Low | Medium | Unit test with known document samples |
| Performance degradation at scale | Medium | Medium | Async processing, caching, batch APIs |

## Dependencies Identified

1. **Azure AI Document Intelligence** - API access and quota
2. **Azure OpenAI Service** - GPT-4 deployment and quota
3. **Azure Cosmos DB** - Database provisioning
4. **Existing entity extraction module** - Extension point

## Open Questions Resolved

All NEEDS CLARIFICATION items from spec resolved in clarification session:

- ✅ Unknown document handling → Reject with manual type specification
- ✅ Confidence threshold for fallback → 70% default, configurable per type
- ✅ Conflicting model values → Flag all values for human review
- ✅ Coordinate system → Normalized (0.0-1.0)
- ✅ Schema storage → Database with versioning (Cosmos DB)
