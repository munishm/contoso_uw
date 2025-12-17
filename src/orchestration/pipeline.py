"""Pipeline builder for creating workflows."""

from typing import Any, Callable, Dict, List, Optional
from src.orchestration.workflow import WorkflowStep, WorkflowOrchestrator


class PipelineBuilder:
    """
    Fluent interface for building processing pipelines.
    
    Simplifies workflow creation with a chainable API.
    """
    
    def __init__(self, name: str):
        """
        Initialize pipeline builder.
        
        Args:
            name: Pipeline name
        """
        self.name = name
        self._steps: List[WorkflowStep] = []
    
    def add_step(
        self,
        step_name: str,
        component: str,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[List[str]] = None,
        error_handler: Optional[Callable] = None,
        skip_on_error: bool = False
    ) -> "PipelineBuilder":
        """
        Add a step to the pipeline.
        
        Args:
            step_name: Name for this step
            component: Component name to execute
            inputs: Input parameters
            outputs: Expected output keys
            error_handler: Optional error handling function
            skip_on_error: Whether to continue on error
            
        Returns:
            Self for chaining
        """
        step = WorkflowStep(
            name=step_name,
            component=component,
            inputs=inputs or {},
            outputs=outputs or [],
            error_handler=error_handler,
            skip_on_error=skip_on_error
        )
        self._steps.append(step)
        return self
    
    def add_classification_step(
        self,
        component: str = "classifier",
        input_key: str = "document"
    ) -> "PipelineBuilder":
        """
        Add a classification step.
        
        Args:
            component: Classifier component name
            input_key: Key for document input
            
        Returns:
            Self for chaining
        """
        return self.add_step(
            step_name="classification",
            component=component,
            inputs={input_key: None},
            outputs=["document_type", "confidence"]
        )
    
    def add_extraction_step(
        self,
        component: str = "extractor",
        input_key: str = "document"
    ) -> "PipelineBuilder":
        """
        Add an entity extraction step.
        
        Args:
            component: Extractor component name
            input_key: Key for document input
            
        Returns:
            Self for chaining
        """
        return self.add_step(
            step_name="extraction",
            component=component,
            inputs={input_key: None},
            outputs=["entities"]
        )
    
    def add_summarization_step(
        self,
        component: str = "summarizer",
        input_key: str = "document"
    ) -> "PipelineBuilder":
        """
        Add a summarization step.
        
        Args:
            component: Summarizer component name
            input_key: Key for document input
            
        Returns:
            Self for chaining
        """
        return self.add_step(
            step_name="summarization",
            component=component,
            inputs={input_key: None},
            outputs=["summary", "key_points"]
        )
    
    def build(self, orchestrator: Optional[WorkflowOrchestrator] = None) -> List[WorkflowStep]:
        """
        Build the pipeline.
        
        Args:
            orchestrator: Optional orchestrator to register with
            
        Returns:
            List of workflow steps
        """
        if orchestrator:
            orchestrator.define_workflow(self.name, self._steps)
        
        return self._steps


def create_document_processing_pipeline() -> PipelineBuilder:
    """
    Create a standard document processing pipeline.
    
    Pipeline includes: classification -> extraction -> summarization
    
    Returns:
        Configured PipelineBuilder
    """
    return (PipelineBuilder("document_processing")
        .add_classification_step()
        .add_extraction_step()
        .add_summarization_step())


def create_classification_only_pipeline() -> PipelineBuilder:
    """
    Create a pipeline that only classifies documents.
    
    Returns:
        Configured PipelineBuilder
    """
    return PipelineBuilder("classification_only").add_classification_step()
