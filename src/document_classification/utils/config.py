"""Configuration for document classification."""

import json
import os
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

# Load .env from document_classification folder (parent of utils)
# Also check for .env in current working directory for flexibility
_env_path = Path(__file__).parent.parent / '.env'
_cwd_env_path = Path.cwd() / '.env'

# Load from both locations, with module-local taking precedence
if _cwd_env_path.exists():
    load_dotenv(_cwd_env_path, override=False)
if _env_path.exists():
    load_dotenv(_env_path, override=True)


class ClassificationMethod(Enum):
    """Available classification methods."""
    DIRECT_CLASSIFICATION = "direct_classification"
    LLM_TEXT = "llm_text"
    LLM_IMAGE = "llm_image"


class Config:
    """Configuration for document classification."""
    
    # Load document categories from JSON file
    _categories_file = Path(__file__).parent / "categories.json"
    with open(_categories_file, 'r', encoding='utf-8') as f:
        DOCUMENT_CATEGORIES = json.load(f)
    
    # Classification method selection
    CLASSIFICATION_METHOD = ClassificationMethod(
        os.getenv("CLASSIFICATION_METHOD", "direct_classification")
    )
    
    # Azure Content Understanding
    CU_ENDPOINT = os.getenv("CU_ENDPOINT")
    AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
    CU_API_VERSION = os.getenv("CU_API_VERSION", "2024-12-01-preview")
    
    # Classifier settings
    CLASSIFIER_ID = "hsbc_insurance_classifier_v6"
    CONFIDENCE_THRESHOLD = 0.5
    
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