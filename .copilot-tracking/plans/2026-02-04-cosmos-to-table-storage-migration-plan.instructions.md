---
applyTo: '.copilot-tracking/changes/2026-02-04-cosmos-to-table-storage-migration-changes.md'
---
<!-- markdownlint-disable-file -->
# Implementation Plan: Migrate Schema Storage from Cosmos DB to Azure Table Storage

## Overview

Replace Cosmos DB with Azure Table Storage for document type schema storage in the entity extraction module to reduce costs and simplify the architecture for low-volume schema management operations.

## Objectives

* Migrate schema repository from Cosmos DB to Azure Table Storage
* Maintain backward compatibility with existing schema models and APIs
* Update configuration and provisioning scripts for Table Storage
* Ensure zero data loss during migration with migration utility
* Reduce monthly costs by ~80% for schema storage operations
* Preserve all existing functionality including versioning and active/inactive states

## Context Summary

### Project Files

* [src/entity_extraction/repositories/schema_repository.py](../../src/entity_extraction/repositories/schema_repository.py) - Current Cosmos DB-based schema repository with document type and version management
* [src/entity_extraction/config.py](../../src/entity_extraction/config.py) - Configuration with Cosmos DB settings (cosmos_endpoint, cosmos_key, cosmos_database, cosmos_container_schemas)
* [src/entity_extraction/models/schema.py](../../src/entity_extraction/models/schema.py) - Schema models (DocumentType, DocumentTypeVersion) using Pydantic with JSON Schema validation
* [src/api/routes/extraction.py](../../src/api/routes/extraction.py) - FastAPI routes using schema repository via dependency injection
* [scripts/setup_extraction_cosmos.py](../../scripts/setup_extraction_cosmos.py) - Cosmos DB provisioning script creating extraction_schemas container
* [infrastructure/bicep/main.bicep](../../infrastructure/bicep/main.bicep) - Infrastructure-as-code defining Cosmos DB resources

### Current Schema Storage Architecture

* Container: `extraction_schemas` with partition key `/document_type_id`
* Two entity types stored: `document_type` and `schema_version`
* DocumentType uses own ID as partition key for efficient lookups
* SchemaVersion partitioned by document_type_id for query efficiency
* Indexing policy excludes input_schema and output_schema paths to reduce costs
* Queries: by name (case-insensitive), by version, by active status, cross-partition for lists

### Azure Table Storage Design

Table Storage is ideal for this use case because:
* Schema access patterns are simple key-value lookups (no complex queries)
* Expected volume is ~10-50 document types with 2-5 versions each
* Read-heavy workload (create schema once, read thousands of times)
* Cost: ~$0.01/GB/month vs Cosmos DB ~$0.25/GB/month + RU charges
* Native JSON support for complex fields via serialization
* Sufficient performance (<50ms reads) for non-critical path

### References

* [Azure Table Storage Python SDK](https://learn.microsoft.com/en-us/azure/cosmos-db/table/how-to-use-python) - azure-data-tables library
* [Cosmos DB vs Table Storage comparison](https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/data-store-comparison) - Cost and feature trade-offs
* [Partition key design for Table Storage](https://learn.microsoft.com/en-us/azure/storage/tables/table-storage-design-guide) - Best practices for partition and row keys

### Standards References

* #file:../../.github/instructions/python-script.instructions.md - Python scripting conventions including async patterns, error handling, and Azure SDK usage
* #file:../../.github/instructions/markdown.instructions.md - Documentation standards for migration guides

## Implementation Checklist

### [ ] Implementation Phase 1: Configuration and Dependencies

<!-- parallelizable: true -->

* [ ] Step 1.1: Add Azure Table Storage configuration to ExtractionConfig
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 25-55)
* [ ] Step 1.2: Add azure-data-tables dependency
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 57-70)
* [ ] Step 1.3: Update environment variable documentation
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 72-90)
* [ ] Step 1.4: Validate phase changes
  * Run lint for modified configuration files
  * Skip full validation due to parallel infrastructure changes

### [ ] Implementation Phase 2: Table Storage Schema Repository

<!-- parallelizable: false -->

* [ ] Step 2.1: Create TableStorageSchemaRepository class
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 92-170)
* [ ] Step 2.2: Implement DocumentType operations (CRUD)
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 172-220)
* [ ] Step 2.3: Implement SchemaVersion operations (CRUD)
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 222-280)
* [ ] Step 2.4: Implement query operations (by name, by version, list all)
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 282-330)
* [ ] Step 2.5: Validate phase changes
  * Run unit tests for schema repository
  * Test JSON serialization/deserialization

### [ ] Implementation Phase 3: Infrastructure and Provisioning

<!-- parallelizable: true -->

* [ ] Step 3.1: Create Table Storage provisioning script
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 332-380)
* [ ] Step 3.2: Update Bicep infrastructure templates
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 382-420)
* [ ] Step 3.3: Add managed identity permissions for Table Storage
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 422-445)
* [ ] Step 3.4: Validate phase changes
  * Test provisioning script in development environment
  * Verify Bicep template syntax with `az bicep build`

### [ ] Implementation Phase 4: API Integration

<!-- parallelizable: false -->

* [ ] Step 4.1: Update dependency injection in FastAPI routes
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 447-485)
* [ ] Step 4.2: Update SchemaService to use new repository
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 487-510)
* [ ] Step 4.3: Update orchestration interface integration
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 512-535)
* [ ] Step 4.4: Validate phase changes
  * Run API integration tests
  * Test end-to-end extraction workflow

### [ ] Implementation Phase 5: Data Migration

<!-- parallelizable: false -->

* [ ] Step 5.1: Create migration script to export from Cosmos DB
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 537-590)
* [ ] Step 5.2: Create migration script to import to Table Storage
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 592-640)
* [ ] Step 5.3: Add validation and rollback capabilities
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 642-680)
* [ ] Step 5.4: Validate phase changes
  * Test migration with sample data
  * Verify data integrity after migration

### [ ] Implementation Phase 6: Testing and Documentation

<!-- parallelizable: false -->

* [ ] Step 6.1: Update unit tests for Table Storage repository
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 682-720)
* [ ] Step 6.2: Update integration tests
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 722-750)
* [ ] Step 6.3: Create migration runbook documentation
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 752-795)
* [ ] Step 6.4: Update architecture documentation
  * Details: .copilot-tracking/details/2026-02-04-cosmos-to-table-storage-migration-details.md (Lines 797-820)
* [ ] Step 6.5: Validate phase changes
  * Run full test suite
  * Review documentation completeness

### [ ] Implementation Phase 7: Validation

<!-- parallelizable: false -->

* [ ] Step 7.1: Run full project validation
  * Execute all lint commands for Python files
  * Execute pytest for all modified components
  * Run mypy type checking
* [ ] Step 7.2: Fix minor validation issues
  * Iterate on lint errors and type hints
  * Apply fixes directly when corrections are straightforward
* [ ] Step 7.3: Report blocking issues
  * Document issues requiring additional research
  * Provide user with next steps and recommended planning
  * Avoid large-scale refactoring within this phase

## Dependencies

* Python 3.11+
* azure-data-tables >= 12.5.0
* Existing entity extraction module structure
* Azure Storage Account with Table Storage enabled
* Managed identity or storage account key for authentication
* Existing Cosmos DB data for migration

## Success Criteria

* All schema operations work identically through new Table Storage repository
* API endpoints return same response format with no breaking changes
* Migration script successfully transfers all schemas with zero data loss
* Infrastructure provisioning scripts create Table Storage tables automatically
* Unit and integration test coverage maintained at current levels (>80%)
* Migration runbook enables safe production deployment
* Cost reduction verified in Azure billing (expected ~80% reduction for schema storage)
* Performance remains acceptable (<100ms for schema reads)
