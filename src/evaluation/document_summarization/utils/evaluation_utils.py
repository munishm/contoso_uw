"""Utility functions for summary evaluation."""

import re
import json
import logging
from typing import List, Dict, Any
from pathlib import Path


logger = logging.getLogger(__name__)


def split_summary_into_sentences(summary_text: str) -> List[str]:
    """
    Split summary text into sentences while avoiding splitting after abbreviations or initials.
    
    Heuristic:
        - Temporarily protect short dot-terminated tokens (likely abbreviations / initials)
        - Split on punctuation followed by whitespace + capital letter
        - Restore protected tokens
    """
    if not summary_text:
        return []

    # Step 1: Protect short dot-terminated tokens (1-5 chars)
    protected_text = summary_text
    protected_text = re.sub(r'\b(\w{1,5}\.)', lambda m: m.group(1).replace('.', '<DOT>'), protected_text)

    # Step 2: Split on sentence-ending punctuation followed by space + capital
    raw_sentences = re.split(r'([.!?])\s+(?=[A-Z])', protected_text)

    # Step 3: Merge punctuation back and restore dots
    sentences = []
    buffer = ""
    for piece in raw_sentences:
        if piece in ".!?":
            buffer += piece
        else:
            buffer += piece
            restored = buffer.replace("<DOT>", ".").strip()
            if restored:
                sentences.append(restored)
            buffer = ""

    return sentences


def extract_numeric_values(text: str) -> List[float]:
    """
    Extract numeric values from text.
    
    Args:
        text: Input string
        
    Returns:
        List of floats found in text
    """
    return [float(x) for x in re.findall(r'\d+(?:\.\d+)?', text)]


# def normalize_text(text: str) -> list[str]:
#     """
#     Normalize text into lowercase alphanumeric tokens while preserving
#     abbreviations like "U.S.A." or initials like "J.K." as single tokens.
#     """
#     text = text.lower()
    
#     # Replace punctuation **except periods inside abbreviations**
#     # Step 1: temporarily protect abbreviations (letters separated by dots)
#     protected = re.findall(r'(?:[a-z]\.){2,}', text)  # e.g., u.s.a., j.k.
#     for i, abbrev in enumerate(protected):
#         placeholder = f"__ABBR{i}__"
#         text = text.replace(abbrev, placeholder)
    
#     # Step 2: remove remaining non-alphanumeric characters
#     text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
#     # Step 3: restore abbreviations
#     for i, abbrev in enumerate(protected):
#         placeholder = f"__ABBR{i}__"
#         text = text.replace(placeholder, abbrev.replace('.', ''))  # remove dots for token
    
#     # Step 4: split on whitespace
#     return [token for token in text.split() if token]


MONTH_CANONICAL_MAP = {
    "jan": "january",
    "feb": "february",
    "mar": "march",
    "apr": "april",
    "may": "may",
    "jun": "june",
    "jul": "july",
    "aug": "august",
    "sep": "september",
    "sept": "september",
    "oct": "october",
    "nov": "november",
    "dec": "december",
}

def normalize_text(text: str) -> List[str]:
    """
    Normalize text into lowercase alphanumeric tokens while preserving
    abbreviations like "U.S.A." or initials like "J.K." as single tokens.
    """
    text = text.lower()

    # Step 1: temporarily protect abbreviations (letters separated by dots)
    protected = re.findall(r'(?:[a-z]\.){2,}', text)  # e.g., u.s.a., j.k.
    for i, abbrev in enumerate(protected):
        placeholder = f"__ABBR{i}__"
        text = text.replace(abbrev, placeholder)

    # Step 2: remove remaining non-alphanumeric characters
    text = re.sub(r'[^a-z0-9\s]', ' ', text)

    # Step 3: restore abbreviations (remove dots)
    for i, abbrev in enumerate(protected):
        placeholder = f"__ABBR{i}__"
        text = text.replace(placeholder, abbrev.replace('.', ''))

    # Step 4: split on whitespace
    tokens = [token for token in text.split() if token]

    # Step 5: canonicalize month abbreviations
    tokens = [MONTH_CANONICAL_MAP.get(token, token) for token in tokens]

    return tokens


def calculate_average_score(results: List[Dict[str, Any]]) -> float:
    """
    Calculate average score from evaluation results.
    
    Args:
        results: List of evaluation result dictionaries
        
    Returns:
        Average score across all results
    """
    if not results:
        return 0.0
    
    scores = [r.get("score", 0.0) for r in results if r.get("success", True)]
    
    if not scores:
        return 0.0
    
    return sum(scores) / len(scores)


def format_evaluation_report(
    results: Dict[str, Any],
    include_metadata: bool = True
) -> str:
    """
    Format evaluation results into a readable report.
    
    Args:
        results: Dictionary containing evaluation results
        include_metadata: Whether to include metadata in report
        
    Returns:
        Formatted string report
    """
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("SUMMARY EVALUATION REPORT")
    report_lines.append("=" * 80)
    
    # Overall metrics
    if "overall_score" in results:
        report_lines.append(f"\nOverall Score: {results['overall_score']:.2f}")
    
    # Individual evaluator results
    if "evaluations" in results:
        report_lines.append("\nEvaluator Results:")
        for evaluator_name, eval_result in results["evaluations"].items():
            report_lines.append(f"\n  {evaluator_name.upper()}:")
            report_lines.append(f"    Score: {eval_result.get('score', 0.0):.2f}")
            
            if eval_result.get("feedback"):
                report_lines.append(f"    Feedback: {eval_result['feedback']}")
            
            if include_metadata and eval_result.get("metadata"):
                report_lines.append("    Metadata:")
                for key, value in eval_result["metadata"].items():
                    report_lines.append(f"      {key}: {value}")
    
    # Summary text
    if "summary" in results:
        report_lines.append("\nSummary:")
        report_lines.append(f"  {results['summary']}")
    
    report_lines.append("\n" + "=" * 80)
    
    return "\n".join(report_lines)


def save_evaluation_results(
    results: Dict[str, Any],
    output_path: str,
    format: str = "json"
) -> None:
    """
    Save evaluation results to file.
    
    Args:
        results: Dictionary containing evaluation results
        output_path: Path to save results
        format: Output format ('json' or 'txt')
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Evaluation results saved to: {output_file}")
        
        elif format == "txt":
            report = format_evaluation_report(results)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Evaluation report saved to: {output_file}")
        
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'json' or 'txt'.")
    
    except Exception as e:
        logger.error(f"Failed to save evaluation results: {e}")
        raise
