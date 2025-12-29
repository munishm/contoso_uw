# Classification Comparison Notebook

This folder contains the interactive comparison notebook for the document classification system.

## Notebooks

- **classification_comparison.ipynb**: Compares all three classification methods (ACU-Only, ACU+LLM Text, ACU+LLM Image) side-by-side with visualizations and performance metrics.

## Usage

1. Make sure the Python kernel is running
2. Update the test document path in the configuration cell if needed
3. Run all cells sequentially to see:
   - Individual classification results for each method
   - Token usage comparisons
   - Confidence score analysis
   - Per-page classification breakdowns
   - Visual charts and recommendations

## Requirements

- All classification methods configured in parent `.env` file
- Test PDF document available at the specified path
- Required packages: pandas, matplotlib, seaborn (installed automatically via pyproject.toml)
