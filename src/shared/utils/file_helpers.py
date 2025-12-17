"""File handling utilities for document processing."""

from pathlib import Path
from typing import Optional, BinaryIO
import mimetypes


def get_file_extension(file_path: str) -> str:
    """
    Extract file extension from file path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File extension (e.g., 'pdf', 'docx') without the dot
    """
    return Path(file_path).suffix.lstrip('.')


def get_mime_type(file_path: str) -> Optional[str]:
    """
    Determine MIME type of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string (e.g., 'application/pdf') or None if unknown
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type


def read_binary_file(file_path: str) -> bytes:
    """
    Read file contents as binary data.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        File contents as bytes
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(path, 'rb') as f:
        return f.read()


def ensure_directory(dir_path: str) -> Path:
    """
    Ensure directory exists, creating it if necessary.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        Path object for the directory
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    return path.stat().st_size


def is_supported_document(file_path: str, supported_types: Optional[list[str]] = None) -> bool:
    """
    Check if file type is supported for processing.
    
    Args:
        file_path: Path to the file
        supported_types: List of supported extensions (default: pdf, docx, txt)
        
    Returns:
        True if file type is supported, False otherwise
    """
    if supported_types is None:
        supported_types = ['pdf', 'docx', 'doc', 'txt']
    
    extension = get_file_extension(file_path)
    return extension.lower() in supported_types
