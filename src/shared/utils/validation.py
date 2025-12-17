"""Data validation utilities."""

import re
from typing import Any, Optional
from datetime import datetime


def validate_policy_number(policy_number: str) -> bool:
    """
    Validate insurance policy number format.
    
    Args:
        policy_number: Policy number to validate
        
    Returns:
        True if valid format, False otherwise
    """
    # Example format: POL-XXXXX where X is alphanumeric
    pattern = r'^POL-[A-Z0-9]{5,10}$'
    return bool(re.match(pattern, policy_number))


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format (international).
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid format, False otherwise
    """
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    # Check if starts with + and has 10-15 digits
    pattern = r'^\+?[1-9]\d{9,14}$'
    return bool(re.match(pattern, cleaned))


def validate_date_string(date_str: str, format: str = "%Y-%m-%d") -> bool:
    """
    Validate date string against format.
    
    Args:
        date_str: Date string to validate
        format: Expected date format (default: YYYY-MM-DD)
        
    Returns:
        True if valid date string, False otherwise
    """
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False


def validate_confidence_score(score: float) -> bool:
    """
    Validate confidence score is in valid range [0, 1].
    
    Args:
        score: Confidence score to validate
        
    Returns:
        True if in valid range, False otherwise
    """
    return 0.0 <= score <= 1.0


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for file system
    """
    # Remove invalid characters for most file systems
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    # Ensure not empty
    return sanitized if sanitized else 'unnamed'


def validate_json_schema(data: dict, required_keys: list[str]) -> tuple[bool, Optional[list[str]]]:
    """
    Validate dictionary has required keys.
    
    Args:
        data: Dictionary to validate
        required_keys: List of required key names
        
    Returns:
        Tuple of (is_valid, missing_keys)
    """
    missing_keys = [key for key in required_keys if key not in data]
    return (len(missing_keys) == 0, missing_keys if missing_keys else None)


def validate_amount(amount: Any) -> tuple[bool, Optional[float]]:
    """
    Validate and parse monetary amount.
    
    Args:
        amount: Amount value (string or number)
        
    Returns:
        Tuple of (is_valid, parsed_amount)
    """
    try:
        if isinstance(amount, str):
            # Remove currency symbols and commas
            cleaned = re.sub(r'[$,£€]', '', amount)
            parsed = float(cleaned)
        else:
            parsed = float(amount)
        
        return (parsed >= 0, parsed)
    except (ValueError, TypeError):
        return (False, None)
