# Document Summarization Evaluation

This package provides tools and evaluators for assessing the quality of generated summaries from document entity extraction.

## Installation

```bash
# Install the package
pip install -e .

# Optional: Install with rapidfuzz for semantic fidelity evaluation only
# (Entity Coverage and Groundedness use token-based methods - no external deps)
pip install -e ".[evaluation]"
```

## Structure

```
evaluation/document_summarization/
├── __init__.py
├── evaluation_service.py       # Main service wrapper
├── evaluators/                 # Evaluator implementations
│   ├── __init__.py
│   └── base_evaluator.py      # Abstract base class
├── utils/                      # Utility functions
│   ├── __init__.py
│   └── evaluation_utils.py
├── notebooks/                  # Evaluation notebooks
└── README.md
```

## Usage

### Basic Setup

```python
from evaluation.document_summarization import SummaryEvaluationService

# Initialize service
service = SummaryEvaluationService(
    azure_endpoint="https://your-resource.openai.azure.com",
    deployment_name="gpt-4",
    api_version="2024-08-01-preview",
    credential=DefaultAzureCredential()
)

# Register evaluators
# Example: service.register_evaluator(EntityCoverageEvaluator())
# Example: service.register_evaluator(GroundednessEvaluator())
# Example: service.register_evaluator(SemanticFidelityEvaluator())
```

### Evaluate Summary

```python
# Evaluate a summary
result = service.evaluate(
    summary="John Doe is a 35-year-old software engineer...",
    entities={
        "name": "John Doe",
        "age": "35",
        "occupation": "Software Engineer"
    },
    context="Insurance Application Form",
    evaluators=["all"]  # Run all registered evaluators
)

print(f"Overall Score: {result['overall_score']}")
print(f"Evaluations: {result['evaluations']}")
```

### Batch Evaluation

```python
# Evaluate multiple summaries
summaries = [
    {
        "summary": "Summary text 1...",
        "entities": {"name": "John", "age": "30"},
        "context": "Application"
    },
    {
        "summary": "Summary text 2...",
        "entities": {"name": "Jane", "age": "28"},
        "context": "Application"
    }
]

results = service.evaluate_batch(
    summaries=summaries,
    evaluators=["all"]
)
```

## Creating Custom Evaluators

To create a custom evaluator, inherit from `BaseEvaluator`:

```python
from evaluation.document_summarization.evaluators import BaseEvaluator, EvaluationResult

class MyCustomEvaluator(BaseEvaluator):
    def evaluate(
        self,
        summary: str,
        entities: Dict[str, str],
        context: Optional[str] = None,
        **kwargs
    ) -> EvaluationResult:
        # Implement your evaluation logic
        score = 0.0  # Calculate score
        feedback = "Evaluation feedback"
        
        return EvaluationResult(
            summary=summary,
            score=score,
            feedback=feedback,
            metadata={"custom_metric": value},
            success=True
        )
    
    def get_evaluator_name(self) -> str:
        return "custom_evaluator"
```

Then register it with the service:

```python
service.register_evaluator(MyCustomEvaluator())
```

## Implemented Evaluators

The framework includes three core evaluators:

1. **Entity Coverage (ECS)** - Weight: 40%
   - Measures entity recall using weighted scoring
   - Auto-weights based on information density: `w = log(1 + tokens) + α·log(1 + chars_per_token)`
   - Uses token overlap (70% threshold) to determine coverage
   - Tracks which entities are covered vs missing
   - **No external dependencies** - uses shared normalize_text() utility

2. **Groundedness (GS)** - Weight: 35%
   - Verifies facts are grounded in source entities
   - **Numeric entities**: Relative deviation penalty (exact or close match)
   - **Textual entities**: Token containment (support-based scoring)
   - Formula: `support = |entity_tokens ∩ sentence_tokens| / |entity_tokens|`
   - **No fuzzy matching** - pure token overlap approach
   - **No external dependencies** - uses shared utilities (split_summary_into_sentences, extract_numeric_values, normalize_text)

3. **Semantic Fidelity (SEF)** - Weight: 25%
   - Measures how faithfully entity values are expressed
   - **Numeric-heavy entities**: Strict grounding with partial_ratio matching
   - **Textual entities**: Fuzzy matching with token_set_ratio
   - **Neutralized verbosity dampening**: No aggressive length penalties (returns 1.0)
   - Uses RapidFuzz for fuzzy matching (optional - falls back to token overlap)
   - Handles natural language variation without penalizing structured summaries

## Utilities

Shared utilities in `utils/evaluation_utils.py`:

- `split_summary_into_sentences(text)`: Split text into sentences using regex
- `extract_numeric_values(text)`: Extract all numeric values from text
- `normalize_text(text)`: Convert text to lowercase alphanumeric tokens
- `calculate_average_score()`: Compute average scores across results
- `format_evaluation_report()`: Generate human-readable reports
- `save_evaluation_results()`: Save results to JSON or text files

All evaluators use these shared utilities to ensure consistency and eliminate code duplication.

## Dependencies

**Required:**
- `pydantic>=2.5.0`: For data validation and result models

**Optional:**
- `rapidfuzz>=3.0.0`: For semantic fidelity fuzzy matching (SEF evaluator only)
  - If not installed, SEF falls back to token overlap similarity
  - Entity Coverage and Groundedness do not require rapidfuzz
- `azure-identity`: For Azure authentication (if using Azure services)
- `openai`: For future LLM-based evaluators

**Note**: The core evaluation framework (ECS + GS) works with standard library only - no external fuzzy matching dependencies required!
