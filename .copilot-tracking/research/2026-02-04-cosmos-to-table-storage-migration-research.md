<!-- markdownlint-disable-file -->
# Research: Cosmos DB to Table Storage Migration for Schema Storage

## Executive Summary

This document analyzes the migration of document type schema storage from Azure Cosmos DB to Azure Table Storage in the Contoso underwriting platform's entity extraction module.

**Recommendation**: Proceed with migration to Table Storage for schema storage only, keeping Cosmos DB for other workloads.

**Expected Benefits**:
* 80% cost reduction for schema storage ($0.01/GB/month vs $0.25/GB/month + RU charges)
* Simplified architecture for low-volume, key-value storage pattern
* Maintained performance (<50ms reads) sufficient for non-critical path

**Risks**: JSON field serialization complexity, query capabilities limited vs Cosmos DB

## Current State Analysis

### Cosmos DB Schema Storage

**Container**: `extraction_schemas`
* Partition key: `/document_type_id`
* Two entity types: `document_type` and `schema_version`
* Expected volume: 10-50 document types, 2-5 versions each (~500 KB total)
* Access pattern: Read-heavy (create once, read thousands of times)
* Current cost: ~$5-10/month (400 RU/s minimum + storage)

**Data Models**:
* DocumentType: 7 fields (id, name, description, created_at, created_by, is_active)
* DocumentTypeVersion: 11 fields including large JSON schemas (input_schema, output_schema, extraction_config)

**Query Patterns**:
1. Get document type by ID (partition key lookup)
2. Get document type by name (cross-partition query with filter)
3. Get schema version by document_type_id + version (partition + filter)
4. List all document types (cross-partition scan)
5. List schema versions for document type (partition scan)

**Current Implementation Files**:
* `src/entity_extraction/repositories/schema_repository.py` - 162 lines, Cosmos SDK
* `src/entity_extraction/config.py` - Configuration with Cosmos settings
* `scripts/setup_extraction_cosmos.py` - Provisioning script

### Access Pattern Characteristics

| Characteristic | Schema Storage | Cases/Documents/Entities |
|----------------|----------------|--------------------------|
| Volume | Low (~50 records) | High (1000s) |
| Read/Write Ratio | 1000:1 | 10:1 |
| Query Complexity | Simple (key-value) | Complex (joins, filters) |
| Latency Requirement | <100ms acceptable | <50ms required |
| Schema Stability | High | Evolving |

**Conclusion**: Schema storage is over-engineered for its access pattern.

## Azure Table Storage Analysis

### Technical Capabilities

**Storage Model**:
* Key-value store with PartitionKey + RowKey as composite primary key
* Entity properties: up to 252 custom properties per entity
* Property size limit: 64 KB per property (sufficient for JSON schemas)
* No secondary indexes (queries scan partition or full table)

**SDK**: `azure-data-tables` (v12.5.0+)
* Async support via `TableClient` and `TableServiceClient`
* Supports managed identity authentication
* Batch operations available (up to 100 entities per batch)

**Cost Model**:
* Storage: $0.01/GB/month (vs Cosmos DB $0.25/GB/month)
* Transactions: $0.0036 per 10,000 transactions
* Expected monthly cost: <$1 for schema storage

### Partition Key Design

**Proposed Design**:

DocumentTypes table:
* PartitionKey: `"DOCTYPE"` (constant - all types in same partition)
* RowKey: `str(document_type_id)` (UUID as string)
* Rationale: Low volume (<100 types) fits in single partition, simple list operations

SchemaVersions table:
* PartitionKey: `str(document_type_id)` (group versions by document type)
* RowKey: `version` (e.g., "1.0.0", "2024")
* Rationale: Efficient version listing per document type, natural partition boundary

**Partition Size Analysis**:
* DocumentTypes: ~50 records × 500 bytes = 25 KB (well under 20 GB limit)
* SchemaVersions: ~250 records × 2 KB (with JSON) = 500 KB per document type (acceptable)

### Performance Comparison

| Operation | Cosmos DB | Table Storage | Impact |
|-----------|-----------|---------------|--------|
| Get by ID | <10ms | <20ms | Acceptable |
| Query by name | <20ms | <50ms (partition scan) | Acceptable |
| List all | <30ms | <100ms (full table scan) | Acceptable |
| Complex queries | Full support | Limited | Not needed for schemas |

**Conclusion**: Performance sufficient for schema storage use case (not in hot path).

## Migration Strategy

### Approach: Parallel Run + Cutover

1. **Phase 1**: Implement Table Storage repository alongside Cosmos DB repository
2. **Phase 2**: Deploy with feature flag (use Cosmos DB in production)
3. **Phase 3**: Run migration script to populate Table Storage
4. **Phase 4**: Validate data integrity
5. **Phase 5**: Cutover to Table Storage (update feature flag)
6. **Phase 6**: Monitor for 1 week
7. **Phase 7**: Decommission Cosmos DB container if successful

### Migration Tooling

**Export from Cosmos DB**:
* Query all entities with `type = 'document_type'` and `type = 'schema_version'`
* Save to timestamped JSON backup files
* Validate export completeness

**Import to Table Storage**:
* Transform Cosmos DB documents to Table Storage entities
* Serialize complex JSON fields (input_schema, output_schema, extraction_config)
* Batch insert with error handling
* Validate import completeness

**Validation**:
* Count comparison (Cosmos vs Table)
* Spot check key records
* Query pattern validation (ensure all queries still work)

### Rollback Plan

If issues discovered after cutover:
1. Update feature flag to revert to Cosmos DB
2. Redeploy application
3. Cosmos DB data still intact (no deletion until 30 days post-cutover)

## JSON Field Handling

### Challenge

DocumentTypeVersion contains large JSON fields:
* `input_schema`: JSON Schema definition (1-5 KB)
* `output_schema`: JSON Schema definition (1-5 KB)
* `extraction_config`: Model configuration (500 bytes)

Table Storage stores properties as strings, so JSON must be serialized.

### Solution

**Serialization**:
```python
entity["input_schema"] = json.dumps(version.input_schema)
entity["output_schema"] = json.dumps(version.output_schema)
entity["extraction_config"] = json.dumps(version.extraction_config)
```

**Deserialization**:
```python
version.input_schema = json.loads(entity["input_schema"])
version.output_schema = json.loads(entity["output_schema"])
version.extraction_config = json.loads(entity["extraction_config"])
```

**Size Validation**: Pre-serialization check ensures JSON < 32 KB (well under 64 KB limit).

## Case-Insensitive Name Lookup

### Challenge

Current Cosmos DB query uses `LOWER()` function for case-insensitive name matching:
```sql
SELECT * FROM c WHERE LOWER(c.name) = LOWER(@name)
```

Table Storage doesn't support string functions in queries.

### Solution

**Two-step approach**:
1. Try exact match with filter: `name eq '{name}'`
2. If no results, query all active types and filter in code:
   ```python
   entities = [e for e in table.query_entities("PartitionKey eq 'DOCTYPE' and is_active eq true")
               if e["name"].lower() == name.lower()]
   ```

**Performance**: Acceptable for <100 document types (full scan <50ms).

## Dependencies and Compatibility

### Python Package Dependencies

**Add**:
* `azure-data-tables>=12.5.0`

**Keep** (for other components):
* `azure-cosmos` (still used for cases, documents, entities, extraction results)

**No conflicts**: Both packages use `azure-core` and compatible credential types.

### Configuration Changes

**New environment variables**:
```bash
EXTRACTION_TABLE_STORAGE_ACCOUNT_NAME=<account>
EXTRACTION_TABLE_STORAGE_ENDPOINT=https://<account>.table.core.windows.net/
EXTRACTION_TABLE_STORAGE_CONNECTION_STRING=<dev-only>
```

**Keep during migration** (deprecated after cutover):
```bash
EXTRACTION_COSMOS_ENDPOINT=...
EXTRACTION_COSMOS_KEY=...
EXTRACTION_COSMOS_DATABASE=...
```

### Infrastructure Changes

**Bicep updates**:
* Enable Table Storage on existing storage account
* Create tables: `DocumentTypes`, `SchemaVersions`
* Add RBAC role assignment: `Storage Table Data Contributor`

**No new resources required**: Use existing storage account.

## Testing Strategy

### Unit Tests

**New tests**:
* `test_table_schema_repository.py`: All CRUD operations
* JSON serialization/deserialization
* Error handling (not found, duplicate key)

**Mocking**: Use Azure Storage Emulator or in-memory mock for fast tests.

### Integration Tests

**Scenarios**:
1. End-to-end API test: Create schema, retrieve, use in extraction
2. Migration test: Export from Cosmos, import to Table, validate
3. Performance test: Measure query latency with realistic data volume

**Test environment**: Dedicated Azure resources (not production).

### Migration Validation

**Checklist**:
* [ ] All document types migrated (count match)
* [ ] All schema versions migrated (count match)
* [ ] JSON fields intact (spot check 5 schemas)
* [ ] All API endpoints functional
* [ ] Extraction workflow works end-to-end
* [ ] No errors in application logs

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| JSON serialization bugs | High | Low | Extensive unit tests, validation script |
| Query performance degradation | Medium | Low | Load test before cutover, rollback plan |
| Data loss during migration | High | Very Low | Backup to JSON files, no Cosmos deletion for 30 days |
| Incompatibility with future features | Medium | Medium | Document query limitations, revisit if needs change |

## Alternatives Considered

### Alternative 1: Keep Cosmos DB

**Pros**: No migration effort, proven solution
**Cons**: Higher cost for simple use case, over-engineered

**Verdict**: Not recommended. Cost not justified for key-value storage.

### Alternative 2: Azure SQL Database

**Pros**: Rich query capabilities, strong consistency
**Cons**: Higher cost than Table Storage, requires schema management, connection pooling

**Verdict**: Not recommended. Overkill for simple schema storage.

### Alternative 3: Blob Storage (JSON files)

**Pros**: Lowest cost (~$0.002/GB/month)
**Cons**: No atomic updates, no querying, concurrency issues

**Verdict**: Not recommended. Lacks transactional guarantees.

### Alternative 4: Redis Cache

**Pros**: Extremely fast (<1ms reads), built-in TTL
**Cons**: Higher cost, in-memory only (requires backup strategy), not designed for persistent storage

**Verdict**: Not recommended. Schemas need persistent storage, not cache.

## Cost-Benefit Analysis

### Current Cost (Cosmos DB)

* Provisioned throughput: 400 RU/s = $23.36/month
* Storage: 1 GB = $0.25/month
* **Total: ~$23.61/month**

Note: Shared with extraction results, so not full cost attributable to schemas alone. Estimated schema-only cost: $5-10/month.

### Projected Cost (Table Storage)

* Storage: 0.001 GB = $0.00001/month
* Transactions: 100,000/month = $0.036/month
* **Total: ~$0.04/month**

### Savings

* **Monthly savings: ~$5-10** (for schema storage only)
* **Annual savings: ~$60-120**
* **ROI**: Positive after 2 months (assuming 20 hours implementation at $100/hr)

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| 1. Configuration & Dependencies | 2 hours | None |
| 2. Table Storage Repository | 8 hours | Phase 1 |
| 3. Infrastructure & Provisioning | 4 hours | Phase 1 (parallel) |
| 4. API Integration | 3 hours | Phase 2 |
| 5. Data Migration | 5 hours | Phases 2, 3 |
| 6. Testing & Documentation | 6 hours | Phase 5 |
| 7. Validation | 2 hours | Phase 6 |
| **Total Development** | **30 hours** | |
| Production Migration (off-hours) | 2 hours | All phases |
| Monitoring period | 1 week | Migration complete |

## Recommendations

### Proceed with Migration

**Reasons**:
1. Access patterns well-suited to Table Storage (key-value, read-heavy)
2. Cost savings significant relative to effort
3. Low risk with comprehensive testing and rollback plan
4. No impact on other system components

### Scope Boundaries

**In scope**: Schema storage only (document types and schema versions)

**Out of scope**:
* Cases, documents, entities (keep in Cosmos DB - different access patterns)
* Extraction results (keep in Cosmos DB - requires complex queries)
* Extraction models registry (evaluate separately - may benefit from Table Storage)

### Post-Migration Actions

1. Monitor performance metrics for 1 week
2. Validate cost reduction in Azure billing
3. Update runbooks and documentation
4. Decommission Cosmos DB extraction_schemas container after 30 days
5. Consider migrating extraction_models container (similar pattern)

## References

* [Azure Table Storage Overview](https://learn.microsoft.com/en-us/azure/storage/tables/table-storage-overview)
* [Table Storage Design Guide](https://learn.microsoft.com/en-us/azure/storage/tables/table-storage-design-guide)
* [azure-data-tables Python SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/data-tables-readme)
* [Cosmos DB vs Table Storage Comparison](https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/data-store-comparison)
* Project files: `src/entity_extraction/repositories/schema_repository.py`, `src/entity_extraction/models/schema.py`
