"""
Example script demonstrating the summarization workflow step.

This script shows how to:
1. Load entity data from evaluation files (label.json format)
2. Use the SummarizationProcessor in a workflow
3. Generate natural language summaries from extracted entities

The data format follows the pattern from evaluations/notebooks/data/label.json
"""

import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.document_summarization.utils.entity_loader import EntityLoader
from src.document_summarization.summarization_service import SummarizationService
from azure.identity import DefaultAzureCredential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_evaluation_entities(label_file_path: str) -> dict:
    """
    Load entities from evaluation label.json file.
    
    Args:
        label_file_path: Path to label.json file in format:
            [
                {
                    "page_number": 1,
                    "entity_presence": {"Entity Name": true},
                    "entity_value": {"Entity Name": "value"},
                    "chinese_entity_value": {}
                },
                ...
            ]
    
    Returns:
        Dictionary of entity names to values
    """
    try:
        entities = EntityLoader.load_and_extract(label_file_path)
        logger.info(f"Loaded {len(entities)} entities from {label_file_path}")
        return entities
    except Exception as e:
        logger.error(f"Error loading entities: {e}")
        raise


def generate_summary_from_entities(entities: dict, document_type: str = "Application Form") -> dict:
    """
    Generate a natural language summary from entities.
    
    Args:
        entities: Dictionary of entity names to values
        document_type: Type of document for context
        
    Returns:
        Dictionary with summary, success status, and metadata
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Get Azure OpenAI configuration
        azure_endpoint = os.getenv("GPT_4_1_API_ENDPOINT")
        deployment_name = os.getenv("GPT_4_1_API_DEPLOYMENT")
        api_version = os.getenv("GPT_4_1_API_VERSION")
        
        if not all([azure_endpoint, deployment_name, api_version]):
            raise ValueError("Azure OpenAI configuration not found in environment variables")
        
        # Initialize SummarizationService
        logger.info("Initializing SummarizationService...")
        service = SummarizationService(
            azure_endpoint=azure_endpoint,
            deployment_name=deployment_name,
            api_version=api_version,
            credential=DefaultAzureCredential(),
            temperature=0.0,
            max_tokens=5000
        )
        
        # Generate summary
        logger.info(f"Generating summary for {len(entities)} entities...")
        result = service.generate_summary(
            entities=entities,
            context=document_type
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise


def demo_summarization_workflow():
    """
    Demonstrate the complete summarization workflow.
    
    This mimics what happens in the workflow when:
    1. Extraction step produces entity data
    2. Summarization step processes those entities
    """
    logger.info("=" * 80)
    logger.info("SUMMARIZATION WORKFLOW DEMO")
    logger.info("=" * 80)
    
    # Example: Load entities from evaluation data
    # In the real workflow, this would come from the extraction step output
    label_file = project_root / "src" / "evaluation" / "entity_extraction" / "notebooks" / "data" / "labels.json"
    
    if not label_file.exists():
        logger.error(f"Label file not found: {label_file}")
        logger.info("Please ensure the evaluation data file exists at the expected location")
        return
    
    # Step 1: Load entities (simulating extraction step output)
    logger.info("\n" + "=" * 80)
    logger.info("STEP 1: Loading Entities from Evaluation Data")
    logger.info("=" * 80)
    entities = load_evaluation_entities(str(label_file))
    
    # Display loaded entities
    logger.info("\nExtracted Entities:")
    logger.info("-" * 80)
    for name, value in entities.items():
        logger.info(f"  {name:<45}: {value}")
    logger.info(f"\nTotal: {len(entities)} entities")
    
    # Step 2: Generate summary (this is what SummarizationProcessor does)
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: Generating Summary")
    logger.info("=" * 80)
    result = generate_summary_from_entities(entities, "Insurance Application Form")
    
    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY RESULT")
    logger.info("=" * 80)
    
    if result["success"]:
        logger.info(f"\n{result['summary']}\n")
        logger.info("-" * 80)
        logger.info("Metadata:")
        for key, value in result["metadata"].items():
            logger.info(f"  {key}: {value}")
    else:
        logger.error(f"\n⚠ Error: {result['error_message']}")
    
    logger.info("\n" + "=" * 80)
    logger.info("DEMO COMPLETE")
    logger.info("=" * 80)
    
    return result


def simulate_workflow_step_output():
    """
    Simulate what the SummarizationProcessor receives from the extraction step.
    
    This shows the expected data format for the summarization step.
    """
    # This is what the extraction step would output
    extraction_output = {
        "extracted_entities": [
            {
                "document_type": "Application Form",
                "file_path": "/path/to/application.pdf",
                "extraction_result": {
                    "status": "success",
                    "entities": [
                        {"type": "Applicant Name", "value": "Ms LOK WING CHING"},
                        {"type": "Job Title of Applicant", "value": "DIRECTOR"},
                        {"type": "Business Registration Number of Employer", "value": "21893829"},
                        {"type": "Height of Applicant", "value": "174 cm"},
                        {"type": "Weight of Applicant", "value": "77 kg"}
                    ]
                },
                "status": "success"
            }
        ],
        "classification_response": None
    }
    
    logger.info("=" * 80)
    logger.info("SIMULATED WORKFLOW DATA FORMAT")
    logger.info("=" * 80)
    logger.info("\nExtraction Step Output (Input to Summarization):")
    logger.info(json.dumps(extraction_output, indent=2))
    
    return extraction_output


if __name__ == "__main__":
    try:
        # Run the demo
        demo_summarization_workflow()
        
        # Show expected data format
        print("\n" + "=" * 80)
        simulate_workflow_step_output()
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
