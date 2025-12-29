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
    CLASSIFIER_ID = "hsbc_insurance_classifier_v3"
    CONFIDENCE_THRESHOLD = 0.5
    
    # Document categories
    DOCUMENT_CATEGORIES = {
    # ───────────── Medical ─────────────
    "Lab Report": "Laboratory test reports containing test results, lab measurements, blood work, pathology results, or any documents with numerical medical test values and reference ranges.",
    
    "Medical Report": "Medical reports including diagnostic imaging results (X-rays, MRIs, CT scans, ultrasounds), radiology reports, physician examination findings, and diagnostic assessments.",
    
    "Medical Letter": "Doctor-written narrative correspondence including consultation notes, referral letters, medical opinions, and recommendations, usually free-text and may contain handwriting.",
    
    "Medical Questionnaire": "Medical declaration forms or health questionnaires completed by the applicant, including medical history, family history, and health disclosures.",

    "Certificate": "Medical certificates, disability certificates, fitness certificates, sick leave certificates, or certified medical statements.",

    # ───────────── Insurance / Policy ─────────────
    "Application": "Insurance application forms submitted by individuals or businesses to request coverage, including personal details, coverage requirements, declarations, and supporting information.",
    
    "Proposal": "Insurance illustration or proposal documents outlining proposed coverage, benefits, premium details, and policy options prior to issuance.",
    
    "Policy": "Insurance policy contracts and agreements outlining coverage terms, conditions, benefits, exclusions, endorsements, and policy details.",
    
    "Declaration": "Customer declarations and acknowledgements such as customer protection declaration, replacement declaration, continued insurability declaration, or beneficiary-related declarations.",
    
    "Important Facts Statement": "Regulatory disclosure documents explaining key facts, risks, financing arrangements, or replacement implications related to insurance products.",

    # ───────────── Financial ─────────────
    "Invoice": "Medical or insurance billing invoices with itemized costs, charges for services, treatments, procedures, and payment information.",
    
    "Receipt": "Proof of payment, transaction confirmations, premium payment receipts, or bank payment acknowledgements.",
    
    "Financial Questionnaire": "Financial assessment forms capturing income, assets, liabilities, net worth, premium affordability, and funding source.",
    
    "Financial Statement": "Formal financial documents such as balance sheets, profit and loss statements, net worth statements, or audited financial reports.",
    
    "Bank Document": "Documents issued by banks such as banker’s memo, bank confirmation letters, account statements, or financing letters.",

    # ───────────── Identity / Travel ─────────────
    "ID Document": "Government-issued identity documents such as passport, national ID card, HKID, PRC ID, or residence permit.",
    
    "Entry Proof": "Travel or immigration documents such as entry permit, visa, arrival slip, or visitor entry proof.",

    # ───────────── Corporate / CMB ─────────────
    "Corporate Document": "Corporate registration and legal documents such as certificate of incorporation, business registration certificate, memorandum and articles of association, partnership agreements.",
    
    "Authorization Document": "Corporate authorization forms, board resolutions, power of attorney, or documents authorizing representatives to act on behalf of an entity.",
    
    "Charge / Registration Document": "Documents related to company charges or securities including NM1, certificate of registration of charge, or charge over assets.",

    # ───────────── Tax & Regulatory ─────────────
    "Tax Form": "Tax residency and compliance forms such as FATCA, CRS, CRS-I, CRS-E, CRS-CP, self-certification forms, and non-FFE declarations.",
    
    "Regulatory Form": "Regulatory or compliance-driven forms required by law or financial institutions that do not fall under tax or insurance applications.",

    # ───────────── General ─────────────
    "Letter": "Non-medical formal correspondence including business letters, explanations, confirmations, or supporting written statements.",
    
    "Manual": "User guides, instruction manuals, product brochures, or reference documentation.",
    
    "Other": "Documents that do not clearly fit any of the above categories or contain mixed/ambiguous content."
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
