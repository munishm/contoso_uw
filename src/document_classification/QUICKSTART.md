# Quick Start Guide - Document Classification

## Prerequisites

- Python 3.11+
- Azure Content Understanding resource with a trained classifier

## Setup (5 minutes)

### 1. Install Dependencies
```bash
cd src/document_classification
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` file:
```bash
# Azure Content Understanding
CU_ENDPOINT=https://your-resource.cognitiveservices.azure.com
AZURE_TENANT_ID=your-tenant-id
CU_CLASSIFIER_ID=hsbc_insurance_classifier_v3
```

### 3. Authenticate with Azure
```bash
az login
```

## Run Classification

### Basic Usage
```python
from document_classification.document_classifier import DirectDocumentClassifier
from document_classification.utils.config import Config

# Initialize
classifier = DirectDocumentClassifier(Config())

# Classify a document
result = classifier.classify('/path/to/your/document.pdf')

# View results
print(f"Pages: {len(result.pages)}")
for page in result.pages:
    print(f"Page {page.page_number}: {page.predicted_label} ({page.confidence:.2f})")
```

### With Document Splitting
```python
from document_classification.utils.split_document import split_document_from_response

# After classification
split_files = split_document_from_response(result, output_dir='./output')

print("Split documents:")
for doc_type, filepath in split_files.items():
    print(f"- {doc_type}: {filepath}")
```

### Using Jupyter Notebook
```bash
# Open the testing notebook
jupyter notebook notebooks/document_classification.ipynb
```

## Test It Works

```python
# Quick test
python -c "from document_classification.document_classifier import DirectDocumentClassifier; print('✅ Ready to classify!')"
```

That's it! You're ready to classify documents.

## Need Help?

- View example usage in [notebooks/](notebooks/)
- Common issues usually involve Azure authentication - make sure `az login` is completed