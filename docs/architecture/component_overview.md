# Component Architecture Overview

## System Architecture

The Contoso Insurance Underwriting Automation Platform follows a **monorepo architecture** with **pluggable components** that communicate through well-defined interfaces. This design enables independent development, testing, and deployment of components while maintaining system coherence.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                      │
│  (Workflow Coordination & Human-in-the-Loop)                │
└──────────────┬──────────────────────────┬──────────────────┘
               │                          │
               ▼                          ▼
    ┌──────────────────┐      ┌──────────────────┐
    │   Classification │      │    Extraction    │
    │    Component     │      │    Component     │
    └──────────────────┘      └──────────────────┘
               │                          │
               └──────────┬───────────────┘
                          ▼
               ┌──────────────────┐
               │  Summarization   │
               │    Component     │
               └──────────────────┘
                          │
                          ▼
               ┌──────────────────┐
               │  Shared Utilities │
               │   & Interfaces    │
               └──────────────────┘
```

## Core Components

### 1. Document Classification
**Purpose**: Determines document type for appropriate routing  
**Location**: `src/document_classification/`  
**Interface**: `IClassifier`, `IDocumentProcessor`  
**Deployable**: Yes (independent)

**Key Functions**:
- Multi-class document type classification
- Confidence scoring
- Fallback to human review for low confidence

### 2. Entity Extraction
**Purpose**: Extracts structured data from unstructured documents  
**Location**: `src/entity_extraction/`  
**Interface**: `IEntityExtractor`, `IDocumentProcessor`  
**Deployable**: Yes (independent)

**Key Functions**:
- Named entity recognition (NER)
- Domain-specific entity extraction (policy numbers, dates, amounts)
- Relationship mapping between entities

### 3. Document Summarization
**Purpose**: Generates concise summaries for quick review  
**Location**: `src/document_summarization/`  
**Interface**: `ISummarizer`, `IDocumentProcessor`  
**Deployable**: Yes (independent)

**Key Functions**:
- Extractive and abstractive summarization
- Key point extraction
- Template-based summaries by document type

### 4. Orchestration
**Purpose**: Coordinates workflow across components  
**Location**: `src/orchestration/`  
**Interface**: `IOrchestrator`  
**Deployable**: Yes

**Key Functions**:
- Component registration and discovery
- Workflow pipeline definition
- Error handling and retry logic
- Human-in-the-loop integration points
- Audit logging

## Shared Infrastructure

### Interfaces (`src/interfaces/`)
Central contracts that define how components interact:
- `IDocumentProcessor`: Base processor interface
- `IClassifier`: Classification contract
- `IEntityExtractor`: Extraction contract
- `ISummarizer`: Summarization contract
- `IOrchestrator`: Orchestration contract

### Shared Utilities (`src/shared/`)
Common code reused across components:
- `utils/`: File helpers, validation, formatting
- `models/`: Shared data models (Document, Entity)
- `schemas/`: JSON schemas for validation
- `config/`: Environment configuration loaders

## Communication Pattern

Components use the **Orchestrator Pattern** for coordination:

1. **Orchestrator** receives document
2. **Orchestrator** calls **Classification** component
3. Based on document type, **Orchestrator** determines pipeline
4. **Orchestrator** calls **Extraction** and **Summarization** in sequence or parallel
5. **Orchestrator** aggregates results and returns to caller

**Benefits**:
- Clear workflow visibility
- Centralized error handling
- Easy to add HITL checkpoints
- Components remain loosely coupled

## Dependency Layering

Strict import hierarchy enforced by `import-linter`:

```
┌─────────────────────────┐
│      Components         │  ← Can import shared & interfaces
│  (classification, etc.) │
└─────────────────────────┘
           ↓
┌─────────────────────────┐
│   Shared Utilities      │  ← Can import interfaces only
│    (src/shared/)        │
└─────────────────────────┘
           ↓
┌─────────────────────────┐
│      Interfaces         │  ← No src/ imports (stdlib only)
│  (src/interfaces/)      │
└─────────────────────────┘
```

**Rules**:
- Interfaces depend on nothing from src/
- Shared utilities only import from interfaces/
- Components can import from shared/ and interfaces/
- Components MUST NOT import directly from other components

## Deployment Strategy

### POC Phase (Current)
- Monolithic deployment of all components
- Single runtime environment
- Shared Azure resources

### Production Phase (Future)
- Independent component deployment
- Microservices architecture (optional)
- Component-level scaling
- Blue-green deployments per component

## Technology Stack

- **Language**: Python 3.11+
- **Package Management**: UV workspaces
- **Cloud Platform**: Azure
- **AI Services**: Azure OpenAI, Document Intelligence
- **Storage**: Azure Blob Storage
- **Database**: Azure Cosmos DB
- **Orchestration**: LangGraph (optional, under evaluation)

## Quality Attributes

### Extensibility
- New components can be added by implementing interfaces
- Orchestrator automatically discovers registered components
- No changes to existing components required

### Maintainability
- Clear separation of concerns
- Each component has focused responsibility
- Comprehensive documentation per component

### Testability
- Components tested in isolation via interfaces
- Mock implementations for testing
- Integration tests validate component interactions
- E2E tests validate full workflows

### Security
- Zero trust architecture
- Component-level access controls
- Audit logging at orchestration layer
- No hardcoded credentials

## Architecture Decision Records

For detailed rationale behind architectural choices, see:
- [001-monorepo-structure.md](adr/001-monorepo-structure.md)
- [002-component-interfaces.md](adr/002-component-interfaces.md)
- [003-orchestrator-pattern.md](adr/003-orchestrator-pattern.md)

## Future Considerations

- **Event-Driven Architecture**: Migrate to Azure Service Bus for async workflows
- **Component Versioning**: Independent versioning with semantic contracts
- **Multi-Language Support**: Add TypeScript/Node.js components if needed
- **Monitoring**: Azure Monitor integration for observability
