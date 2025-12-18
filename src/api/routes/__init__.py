"""
API route handlers.

This module exports all route modules for registration with the FastAPI app.
"""

from src.api.routes import cases, documents, health, processing

__all__ = ["cases", "documents", "health", "processing"]
