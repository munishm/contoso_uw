"""Utility functions for evaluators."""

import re
from typing import Any


def clean_text(text: str) -> str:
    """
    Clean text by removing HTML tags and normalizing whitespace.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text with HTML removed and normalized whitespace
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove HTML tags
    text = re.sub(r"<.*?>", " ", text)
    
    # Collapse multiple whitespace into single space
    text = re.sub(r"\s+", " ", text)
    
    return text.strip()


def normalize_value(value: Any) -> str:
    """
    Normalize extracted value to string for comparison.
    
    Args:
        value: Value to normalize
        
    Returns:
        String representation of the value
    """
    if value is None:
        return ""
    
    if isinstance(value, (list, tuple)):
        return " ".join(str(v) for v in value)
    
    return str(value)
