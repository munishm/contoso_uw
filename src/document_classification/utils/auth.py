"""Azure authentication utilities."""

import os
import logging
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.core.exceptions import ClientAuthenticationError

# Import shared authentication manager
from .auth_manager import (
    get_shared_credential, 
    create_shared_token_provider,
    get_shared_token
)


logger = logging.getLogger(__name__)


def get_azure_credential(tenant_id: str):
    """
    Get Azure credential for authentication.
    Now uses shared authentication to avoid multiple auth attempts.
    
    Args:
        tenant_id: Azure tenant ID
        
    Returns:
        Azure credential instance
    """
    return get_shared_credential(tenant_id)


def create_token_provider(tenant_id: str):
    """
    Create a token provider function for Azure AD authentication.
    Now uses shared authentication to avoid multiple auth attempts.
    
    Args:
        tenant_id: Azure tenant ID
        
    Returns:
        Callable that returns an access token
    """
    return create_shared_token_provider(tenant_id)
