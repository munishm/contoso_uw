"""Workflow orchestration for document processing."""

from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from src.orchestration.registry import registry


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class WorkflowStep:
    """
    Represents a single step in a workflow.
    
    Attributes:
        name: Step name
        component: Component name to execute
        inputs: Input parameters for the component
        outputs: Expected output keys
        error_handler: Optional error handling function
        skip_on_error: Whether to continue workflow if step fails
    """
    name: str
    component: str
    inputs: Dict[str, Any]
    outputs: List[str]
    error_handler: Optional[Callable] = None
    skip_on_error: bool = False


class WorkflowOrchestrator:
    """
    Orchestrates workflows across multiple components.
    
    Coordinates component execution, error handling, and
    human-in-the-loop integration points.
    """
    
    def __init__(self):
        """Initialize workflow orchestrator."""
        self._workflows: Dict[str, List[WorkflowStep]] = {}
        self._results: Dict[str, Any] = {}
        self._status = WorkflowStatus.PENDING
    
    def define_workflow(self, name: str, steps: List[WorkflowStep]) -> None:
        """
        Define a new workflow.
        
        Args:
            name: Workflow name
            steps: List of workflow steps to execute
        """
        self._workflows[name] = steps
    
    def execute(
        self, 
        workflow_name: str, 
        inputs: Dict[str, Any],
        human_review_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow.
        
        Args:
            workflow_name: Name of workflow to execute
            inputs: Initial input data
            human_review_callback: Optional callback for human review
            
        Returns:
            Workflow execution results
            
        Raises:
            KeyError: If workflow not found
            RuntimeError: If workflow execution fails
        """
        if workflow_name not in self._workflows:
            raise KeyError(f"Workflow not found: {workflow_name}")
        
        self._status = WorkflowStatus.RUNNING
        self._results = {}
        workflow = self._workflows[workflow_name]
        
        context = inputs.copy()
        
        try:
            for step in workflow:
                # Get component from registry
                if not registry.has_component(step.component):
                    raise RuntimeError(f"Component not found: {step.component}")
                
                component = registry.get(step.component)
                
                # Prepare step inputs
                step_inputs = {
                    key: context.get(key, value) 
                    for key, value in step.inputs.items()
                }
                
                try:
                    # Execute component
                    result = component.process(step_inputs)
                    
                    # Store outputs in context
                    for output_key in step.outputs:
                        if output_key in result:
                            context[output_key] = result[output_key]
                    
                    # Store step result
                    self._results[step.name] = result
                    
                    # Human review checkpoint if provided
                    if human_review_callback:
                        review_result = human_review_callback(step.name, result)
                        if review_result.get("action") == "pause":
                            self._status = WorkflowStatus.PAUSED
                            return self._results
                
                except Exception as e:
                    if step.error_handler:
                        step.error_handler(e)
                    
                    if not step.skip_on_error:
                        self._status = WorkflowStatus.FAILED
                        raise RuntimeError(f"Step {step.name} failed: {e}")
            
            self._status = WorkflowStatus.COMPLETED
            return self._results
        
        except Exception as e:
            self._status = WorkflowStatus.FAILED
            raise RuntimeError(f"Workflow execution failed: {e}")
    
    def get_status(self) -> WorkflowStatus:
        """
        Get current workflow status.
        
        Returns:
            Current workflow status
        """
        return self._status
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get workflow execution results.
        
        Returns:
            Dictionary of results by step name
        """
        return self._results.copy()
    
    def list_workflows(self) -> List[str]:
        """
        Get list of defined workflows.
        
        Returns:
            List of workflow names
        """
        return list(self._workflows.keys())


# Global orchestrator instance
orchestrator = WorkflowOrchestrator()
