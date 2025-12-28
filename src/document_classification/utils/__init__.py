"""Utilities for document classification."""

from .config import Config, ClassificationMethod
from .factory import create_classifier
from .auth import get_azure_credential, create_token_provider
from .acu_client import AzureContentUnderstandingClient
from .auth_manager import (
    get_shared_credential, 
    create_shared_token_provider, 
    get_shared_token
)

__all__ = [
    'Config',
    'ClassificationMethod',
    'create_classifier',
    'get_azure_credential',
    'create_token_provider',
    'AzureContentUnderstandingClient',
    'get_shared_credential',
    'create_shared_token_provider', 
    'get_shared_token'
]
