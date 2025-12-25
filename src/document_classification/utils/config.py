"""Configuration for document classification."""

import os
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

# Load .env from document_classification folder (parent of utils)
_env_path = Path(__file__).parent.parent / '.env'
if _env_path.exists():
    load_dotenv(_env_path, override=True)


class ClassificationMethod(Enum):
    """Available classification methods."""
    ACU_ONLY = "acu_only"
    ACU_LLM_TEXT = "acu_llm_text"
    LLM_IMAGE = "llm_image"


class Config:
    """Configuration for document classification."""
    
    # Classification method selection
    CLASSIFICATION_METHOD = ClassificationMethod(
        os.getenv("CLASSIFICATION_METHOD", "acu_only")
    )
    
    # Azure Content Understanding
    CU_ENDPOINT = os.getenv("CU_ENDPOINT")
    AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
    CU_API_VERSION = "2025-11-01"
    
    # Azure OpenAI (for LLM methods)
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    
    # Classifier settings
    CLASSIFIER_ID = "hsbc_insurance_classifier_v1"
    CONFIDENCE_THRESHOLD = 0.5
    
    # Document categories
    DOCUMENT_CATEGORIES = {
        "Lab Report": "Laboratory test reports containing test results, lab measurements, blood work, pathology results, or any documents with numerical medical test values and reference ranges.",
        "Medical Report": "Medical reports including diagnostic imaging results (X-rays, MRIs, CT scans, ultrasounds), radiology reports, physician examination findings, and diagnostic assessments.",
        "Invoice": "Medical or insurance billing invoices with itemized costs, charges for services, treatments, procedures, and payment information.",
        "Application": "Insurance application forms submitted by individuals or businesses to request coverage, including personal details, coverage requirements, and supporting documentation.",
        "Policy": "Insurance policy contracts and agreements outlining coverage terms, conditions, benefits, exclusions, and policy details.",
        "Medical Letter": "Doctor-written narrative correspondence including consultation notes, referral letters, medical opinions, recommendations, usually narrative text written by a physician and may contain handwriting.",
        "Letter": "Non-medical formal correspondence, business or personal letters.",
        "Certificate": "Medical certificates, disability certificates, fitness certificates, or sick leave certificates.",
        "Receipt": "Proof of payment, transaction confirmations, payment receipts.",
        "Manual": "User guides, instruction manuals, documentation.",
        "Other": "Documents that do not clearly fit any of the above categories."
    }
    
    # Output settings
    OUTPUT_DIR = Path(__file__).parent.parent / "output"
    SAVE_RESULTS = True
    
    @classmethod
    def validate(cls):
        """Validate configuration."""
        if not cls.CU_ENDPOINT:
            raise ValueError("CU_ENDPOINT environment variable is required")
        if not cls.AZURE_TENANT_ID:
            raise ValueError("AZURE_TENANT_ID environment variable is required")
        
        # Ensure output directory exists
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
