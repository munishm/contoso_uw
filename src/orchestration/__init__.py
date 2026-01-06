"""Orchestration module for document processing workflows."""

from .workflow import (
    WorkflowOrchestrator,
    WorkflowStep,
    WorkflowStatus,
    orchestrator
)
from .pipeline import (
    PipelineBuilder,
    create_document_processing_pipeline,
    create_classification_only_pipeline
)
from .registry import (
    ComponentRegistry,
    registry
)
from .case_workflow import (
    CaseWorkflowManager,
    WorkflowConfig,
    StepConfig,
    StepType,
    ClassifierProcessor,
    FileUploadProcessor,
    DatabaseUpdateProcessor,
    ExtractionProcessor,
    workflow_manager,
    initialize_case_workflow,
    on_new_case_created,
    create_custom_workflow,
    DEFAULT_CASE_WORKFLOW_CONFIG
)


__all__ = [
    # Workflow
    'WorkflowOrchestrator',
    'WorkflowStep',
    'WorkflowStatus',
    'orchestrator',
    # Pipeline
    'PipelineBuilder',
    'create_document_processing_pipeline',
    'create_classification_only_pipeline',
    # Registry
    'ComponentRegistry',
    'registry',
    # Case Workflow
    'CaseWorkflowManager',
    'WorkflowConfig',
    'StepConfig',
    'StepType',
    'ClassifierProcessor',
    'FileUploadProcessor',
    'DatabaseUpdateProcessor',
    'ExtractionProcessor',
    'workflow_manager',
    'initialize_case_workflow',
    'on_new_case_created',
    'create_custom_workflow',
    'DEFAULT_CASE_WORKFLOW_CONFIG',
]
