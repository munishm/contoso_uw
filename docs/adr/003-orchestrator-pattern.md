# ADR 003: Orchestrator Pattern

**Date**: 2025-12-15  
**Status**: Accepted  
**Deciders**: Platform Team  

## Context

Components need to communicate and coordinate for multi-step document processing workflows. We need an architecture that:
- Enables plug-and-play components
- Supports human-in-the-loop (HITL) integration points
- Provides clear workflow visibility for auditing
- Allows flexible pipeline construction

## Decision

We will use the **Orchestrator Pattern** with a central workflow coordinator:

```
┌────────────────────────┐
│  Workflow Orchestrator │
│  (Central Coordinator) │
└───────┬────────────────┘
        │
    ┌───┴───┐
    │       │
    ▼       ▼
┌─────────┐ ┌─────────┐
│Component│ │Component│
│    A    │ │    B    │
└─────────┘ └─────────┘
```

**Key Decisions**:
1. **Central Orchestrator**: Single workflow coordinator in `src/orchestration/`
2. **Component Registry**: Runtime registration of components
3. **Pipeline Builder**: Fluent API for defining workflows
4. **HITL Integration**: Built-in support for human review checkpoints

## Consequences

### Positive
- Clear workflow visibility - easy to understand processing steps
- HITL integration points naturally fit into orchestration
- Components remain decoupled - communicate only through orchestrator
- Easy to modify pipelines without changing components
- Centralized error handling and logging
- Supports both sequential and parallel execution

### Negative
- Orchestrator can become bottleneck for high-throughput scenarios
- Single point of failure (needs proper error handling)
- More complex than direct component-to-component calls

### Mitigation
- Design for horizontal scaling (multiple orchestrator instances)
- Implement comprehensive error handling and retry logic
- Provide migration path to event-driven architecture for production

## Alternatives Considered

1. **Direct Component Calls**: Components call each other directly
   - Rejected: Creates tight coupling, violates plug-and-play requirement

2. **Event Bus / Pub-Sub**: Components communicate via events
   - Deferred: Too complex for POC, consider for production
   - Migration path preserved through interface abstraction

3. **Saga Pattern**: Distributed transactions with compensation
   - Rejected: Overkill for current requirements

## Implementation Details

Three core modules:

1. **Component Registry** (`src/orchestration/registry.py`):
```python
registry.register("classifier", classifier_instance)
component = registry.get("classifier")
```

2. **Workflow Orchestrator** (`src/orchestration/workflow.py`):
```python
orchestrator.define_workflow("doc_processing", steps)
result = orchestrator.execute("doc_processing", inputs)
```

3. **Pipeline Builder** (`src/orchestration/pipeline.py`):
```python
pipeline = (PipelineBuilder("workflow")
    .add_classification_step()
    .add_extraction_step()
    .build())
```

## Migration Path

For production scale, the orchestrator pattern enables migration to:
- **Azure Service Bus**: Replace in-process calls with async messages
- **Event Grid**: Event-driven architecture for better scalability
- **LangGraph**: State machine-based orchestration (under evaluation)

Interface-based architecture ensures components don't need changes.

## References

- [Research Findings](../../specs/001-project-structure/research.md#research-task-2-component-communication-patterns)
- [Orchestration Pattern](https://microservices.io/patterns/data/saga.html)
